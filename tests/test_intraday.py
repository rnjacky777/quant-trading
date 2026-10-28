from collections import Counter
from dataclasses import replace
import json

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
from app.strategies.base import Action
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from scripts.optimize_backtest import main


def tape(n=300):
    return [Candle("binance", "BTC/USDT", "1h", i*3600000,
                   100+i*.1, 100+i*.1+.01, 100+i*.1-.01, 100+i*.1, 1) for i in range(n)]


def test_daily_entry_limit_counts_fills_and_resets_at_utc_midnight():
    bars = [Candle("binance", "BTC/USDT", "1h", i*3600000, 100, 100, 94, 100, 1) for i in range(49)]
    config = BacktestConfig(stop_loss_pct=.05, max_entries_per_day=2, fee_bps=0, slippage_bps=0)
    result = BacktestEngine(config).run(bars, BuyAndHoldStrategy())
    counts = Counter(t.entry_timestamp_ms//86400000 for t in result.trades)
    assert counts == {0: 2, 1: 2, 2: 1}


def test_time_limit_exits_at_next_open_without_same_bar_reentry():
    config = BacktestConfig(max_holding_bars=3, fee_bps=0, slippage_bps=0)
    result = BacktestEngine(config).run(tape(10), BuyAndHoldStrategy())
    assert result.trades[0].exit_reason == "time_limit"
    assert result.trades[0].entry_timestamp_ms == 3600000
    assert result.trades[0].exit_timestamp_ms == 4*3600000
    assert result.trades[1].entry_timestamp_ms == 5*3600000
    assert result.trades[0].exit_price == tape(10)[4].open


def test_intraday_atr_stop_is_not_overwritten_by_fixed_stop_wrapper():
    config = BacktestConfig(stop_loss_pct=.05, risk_per_trade=.0025, exit_mode="signal")
    strategy = make_strategy("intraday", config)
    bars = tape(243)
    signal = strategy.generate(bars)
    assert signal.action is Action.BUY
    assert signal.stop_loss_price is not None
    assert signal.stop_loss_fraction is None
    assert 0 < signal.stop_loss_price < bars[-1].close
    changed = bars + [replace(bars[-1], timestamp_ms=bars[-1].timestamp_ms+3600000, close=10000, high=10000)]
    assert strategy.generate(changed[:-1]) == signal
    bars = tape(242)
    bars[-2] = replace(bars[-2], open=120, high=120, low=120, close=120)
    bars[-1] = replace(bars[-1], open=126, high=126, low=126, close=126)
    assert make_strategy("intraday", replace(config, intraday_entry="pullback")).generate(bars).action is Action.BUY


def test_cost_feasibility_filter_blocks_small_range_but_keeps_signal_exit():
    config = BacktestConfig(stop_loss_pct=.05, risk_per_trade=.0025, exit_mode="signal")
    bars = tape(243)
    assert make_strategy("intraday", config).generate(bars).action is Action.BUY
    filtered = make_strategy("intraday", replace(config, intraday_min_atr_fraction=.006))
    assert filtered.generate(bars).action is Action.HOLD
    bars[-1] = replace(bars[-1], open=100, high=100, low=100, close=100)
    assert filtered.generate(bars).action is Action.SELL


def test_strong_close_confirms_completed_candle_and_does_not_block_exits():
    config = BacktestConfig(stop_loss_pct=.05, risk_per_trade=.0025, exit_mode="signal", intraday_strong_close=True)
    strategy = make_strategy("intraday", config)
    bars = tape(243)
    assert strategy.generate(bars).action is Action.HOLD  # Doji is not confirmation.
    bars[-1] = replace(bars[-1], open=199, high=201, low=198, close=200)
    signal = strategy.generate(bars)
    assert signal.action is Action.BUY  # Exactly at the upper-third boundary.
    bars[-1] = replace(bars[-1], close=199.99)
    assert strategy.generate(bars).action is Action.HOLD
    bars[-1] = replace(bars[-1], open=100, high=100, low=100, close=100)
    assert strategy.generate(bars).action is Action.SELL


@pytest.mark.parametrize("changes,expected_mode,expected_atr", [
    ({"intraday_entry": "pullback"}, "pullback", 0),
    ({"intraday_min_atr_pct": .6}, "breakout", .006),
    ({"intraday_strong_close": True}, "breakout", 0),
    ({"risk_regime": "loss_streak"}, "breakout", 0),
])
def test_intraday_saved_version_optimizer_and_dashboard_roundtrip(tmp_path, monkeypatch, capsys, changes, expected_mode, expected_atr):
    path = tmp_path / "intraday.sqlite3"
    bars = tape(24*20)
    CandleRepository(path).upsert(bars)
    config = BacktestConfig(stop_loss_pct=.05, risk_per_trade=.0025, exit_mode="signal",
                            max_entries_per_day=2, max_holding_bars=24)
    result = BacktestEngine(config).run(bars, make_strategy("intraday", config))
    repo = BacktestRunRepository(path)
    base = repo.save(result, bars, config, "development", "", None, None)
    task = OptimizationRequestRepository(path).enqueue(base.run_key)
    monkeypatch.setattr("sys.argv", ["optimize", "--db", str(path), "optimize-request", "--request-id", str(task.request_id),
        "--changes-json", json.dumps(changes), "--note", "Only test one fixed signal hypothesis"])
    main()
    payload = json.loads(capsys.readouterr().out)
    child = repo.get_run(payload["candidate"]["run_key"])
    assert repo.get_result(child.run_key)[0] == reproduce_run(path, "binance", child)[2]
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    response = TestClient(app).get("/backtests/run", params=dict(strategy="intraday", strategy_key=child.strategy_key,
        symbol="BTC/USDT", timeframe="1h", since="1970-01-12", until="1970-01-20", max_entries_per_day=10, max_holding_bars=100))
    assert response.status_code == 200
    assert response.context["values"]["max_entries_per_day"] == 2
    assert response.context["values"]["max_holding_bars"] == 24
    assert response.context["values"]["intraday_entry"] == expected_mode
    assert response.context["values"]["intraday_min_atr_pct"] == pytest.approx(expected_atr * 100)
    assert response.context["values"]["intraday_strong_close"] is changes.get("intraday_strong_close", False)
    assert response.context["values"]["risk_regime"] == changes.get("risk_regime", "fixed")
    assert response.context["saved_run"].strategy_key == child.strategy_key
    saved = response.context["saved_run"]
    assert repo.get_result(saved.run_key)[0] == reproduce_run(path, "binance", saved)[2]


@pytest.mark.parametrize("field,value", [("max_holding_bars", 0), ("max_entries_per_day", True)])
def test_entry_and_time_limits_reject_invalid_values(field, value):
    with pytest.raises(ValueError):
        BacktestConfig(**{field: value})
