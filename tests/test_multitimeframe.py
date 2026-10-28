from dataclasses import replace
from datetime import datetime, timezone

from fastapi.testclient import TestClient
import pytest

from app.api.main import app
from app.backtest.configuration import make_strategy
from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.backtest.optimization import OptimizationRequestRepository
from app.backtest.reproduction import reproduce_run
from app.backtest.runs import BacktestRunRepository
from app.data.models import Candle
from app.data.repository import CandleRepository
from app.strategies.base import Action, Signal
from app.strategies.multitimeframe import CompletedFourHourTrend, completed_four_hour_closes
from scripts.optimize_backtest import main


def tape(count=300):
    return [Candle("binance", "BTC/USDT", "1h", i*3600000,
                   100+i/10, 101+i/10, 99+i/10, 100+i/10, 1) for i in range(count)]


def test_incomplete_four_hour_bucket_cannot_change_filter_closes():
    bars = tape(243)
    assert len(completed_four_hour_closes(bars)) == 60
    original = completed_four_hour_closes(bars)
    bars[-1] = replace(bars[-1], close=10000, high=10000)
    assert completed_four_hour_closes(bars) == original
    assert completed_four_hour_closes(tape(244))[-1] == tape(244)[-1].close
    assert len(completed_four_hour_closes(tape(239))) == 59
    assert len(completed_four_hour_closes(tape(244)[1:])) == 60


def test_filter_blocks_only_buys_and_requires_complete_hourly_buckets():
    class Constant:
        name = "test"
        def __init__(self, action):
            self.action = action
        def generate(self, bars):
            return Signal(bars[-1].symbol, datetime.fromtimestamp(bars[-1].timestamp_ms/1000, timezone.utc), self.action, 1, self.name)
    assert CompletedFourHourTrend(Constant(Action.BUY)).generate(tape(239)).action is Action.HOLD
    assert CompletedFourHourTrend(Constant(Action.BUY)).generate(tape(240)).action is Action.BUY
    assert CompletedFourHourTrend(Constant(Action.SELL)).generate(tape(239)).action is Action.SELL
    bars = tape(240)
    bars[-30] = replace(bars[-30], timestamp_ms=bars[-30].timestamp_ms-1)
    with pytest.raises(ValueError, match="incomplete"):
        completed_four_hour_closes(bars)


def test_mtf_candidate_replays_and_dashboard_locks_filter(tmp_path, monkeypatch, capsys):
    path = tmp_path / "mtf.sqlite3"
    bars = tape(24*20)
    CandleRepository(path).upsert(bars)
    config = BacktestConfig(stop_loss_pct=.05, risk_per_trade=.005)
    result = BacktestEngine(config).run(bars, make_strategy("sma", config, fast=2, slow=3))
    repo = BacktestRunRepository(path)
    base = repo.save(result, bars, config, "development", "", 2, 3)
    task = OptimizationRequestRepository(path).enqueue(base.run_key)
    monkeypatch.setattr("sys.argv", ["optimize", "--db", str(path), "optimize-request", "--request-id", str(task.request_id),
        "--changes-json", '{"higher_timeframe_filter":true}', "--note", "Test one fixed completed 4h filter"])
    main()
    payload = __import__("json").loads(capsys.readouterr().out)
    child = repo.get_run(payload["candidate"]["run_key"])
    assert repo.get_result(child.run_key)[0] == reproduce_run(path, "binance", child)[2]
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    response = TestClient(app).get("/backtests/run", params=dict(strategy="sma", strategy_key=child.strategy_key,
        symbol="BTC/USDT", timeframe="1h", since="1970-01-12", until="1970-01-20", higher_timeframe_filter=False))
    assert response.status_code == 200
    assert response.context["values"]["higher_timeframe_filter"] is True
    assert response.context["saved_run"].strategy_key == child.strategy_key
    saved = response.context["saved_run"]
    assert repo.get_result(saved.run_key)[0] == reproduce_run(path, "binance", saved)[2]
