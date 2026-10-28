from dataclasses import replace
from math import prod
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.backtest.configuration import make_strategy
from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.backtest.periods import annual_performance
from app.backtest.reproduction import reproduce_run
from app.backtest.runs import BacktestRunRepository
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository
from scripts.optimize_backtest import main as optimize_main


def seed(path):
    candles = [Candle("binance", "BTC/USDT", "1d", i * TIMEFRAMES_MS["1d"],
                      100 + i % 7, 102 + i % 7, 98 + i % 7, 100 + i % 7, 1)
               for i in range(90)]
    CandleRepository(path).upsert(candles)
    return candles


@pytest.mark.parametrize("family", ["sma", "momentum", "mean-reversion"])
def test_policy_version_replay_and_dashboard_round_trip(tmp_path, monkeypatch, family) -> None:
    database = tmp_path / "test.sqlite3"
    candles = seed(database)
    monkeypatch.setenv("QUANT_DB_PATH", str(database))
    config = BacktestConfig(risk_per_trade=0.005, stop_loss_pct=0.05, take_profit_pct=0.1,
                            exit_mode="signal", max_exposure_fraction=0.2)
    strategy = make_strategy(family, config, fast=2, slow=3, lookback=2)
    result = BacktestEngine(config).run(candles, strategy)
    repo = BacktestRunRepository(database)
    saved = repo.save(result, candles, config, "development", "policy test",
                      2 if family == "sma" else None, 3 if family == "sma" else None)
    replay = reproduce_run(database, "binance", saved)[2]
    assert replay == result
    assert len(repo.list_strategy_versions()) == 1
    client = TestClient(app)
    page = client.get("/")
    assert page.status_code == 200
    assert "0.50%" in page.text
    changed_config = replace(config, risk_per_trade=0.0025)
    changed = BacktestEngine(changed_config).run(candles, make_strategy(family, changed_config, fast=2, slow=3, lookback=2))
    repo.save(changed, candles, changed_config, "development", "risk change", saved.fast_period, saved.slow_period,
              base_run_key=saved.run_key)
    assert len(repo.list_strategy_versions()) == 2
    assert repo.list_strategy_versions()[0].previous_strategy_key == saved.strategy_key


def test_legacy_schema_migration_preserves_results_and_version(tmp_path) -> None:
    database = tmp_path / "legacy.sqlite3"
    candles = seed(database)
    config = BacktestConfig()
    result = BacktestEngine(config).run(candles, make_strategy("sma", config, fast=2, slow=3))
    repo = BacktestRunRepository(database)
    saved = repo.save(result, candles, config, "development", "legacy", 2, 3)
    with sqlite3.connect(database) as connection:
        connection.execute("ALTER TABLE backtest_runs DROP COLUMN policy_json")
        connection.execute("ALTER TABLE backtest_runs DROP COLUMN research_plan_id")
        connection.execute("ALTER TABLE strategy_versions DROP COLUMN policy_json")
    restored = repo.get_run(saved.run_key)
    assert restored.policy_json == "{}"
    assert restored.strategy_key == saved.strategy_key
    assert reproduce_run(database, "binance", restored)[2] == result
    assert len(repo.list_strategy_versions()) == 1


def test_optimizer_preserves_risk_policy_when_reproducing(tmp_path, monkeypatch, capsys) -> None:
    database = tmp_path / "optimizer.sqlite3"
    candles = seed(database)
    config = BacktestConfig(risk_per_trade=0.005, stop_loss_pct=0.05)
    result = BacktestEngine(config).run(candles, make_strategy("sma", config, fast=2, slow=3))
    run = BacktestRunRepository(database).save(result, candles, config, "development", "", 2, 3)
    monkeypatch.setattr("sys.argv", ["optimizer", "--db", str(database), "analyze", "--run-key", run.run_key])
    optimize_main()
    import json
    payload = json.loads(capsys.readouterr().out)
    assert payload["metrics"]["total_return"] == pytest.approx(result.metrics.total_return)


def test_annual_returns_compound_to_full_period_return(tmp_path) -> None:
    candles = seed(tmp_path / "annual.sqlite3")
    config = BacktestConfig()
    result = BacktestEngine(config).run(candles, make_strategy("buy-hold", config))
    rows = annual_performance(result)
    assert prod(1 + row["total_return"] for row in rows) - 1 == pytest.approx(result.metrics.total_return)


def test_dashboard_rejects_leverage_and_requires_stop_for_risk_mode(tmp_path, monkeypatch) -> None:
    database = tmp_path / "test.sqlite3"
    seed(database)
    monkeypatch.setenv("QUANT_DB_PATH", str(database))
    client = TestClient(app)
    params = dict(symbol="BTC/USDT", timeframe="1d", strategy="sma",
                  since="1970-01-01", until="1970-04-01")
    assert client.get("/backtests/run", params={**params, "leverage": 2}).status_code == 422
    assert client.get("/backtests/run", params={**params, "stop_loss_pct": 0, "risk_per_trade_pct": 0.5}).status_code == 422


def test_child_replays_exact_inherited_warmup_and_rejects_changed_data(tmp_path) -> None:
    database = tmp_path / "warmup.sqlite3"
    candles = seed(database)
    config = BacktestConfig()
    repo = BacktestRunRepository(database)
    start = candles[30].timestamp_ms
    signals = candles[27:]
    parent_result = BacktestEngine(config).run(signals, make_strategy("sma", config, fast=2, slow=3), evaluation_start_ms=start)
    parent = repo.save(parent_result, candles[30:], config, "development", "", 2, 3, signal_candles=signals)
    child_result = BacktestEngine(config).run(signals, make_strategy("sma", config, fast=4, slow=6), evaluation_start_ms=start)
    child = repo.save(child_result, candles[30:], config, "development", "", 4, 6, base_run_key=parent.run_key, signal_candles=signals)
    assert reproduce_run(database, "binance", child)[2] == child_result
    CandleRepository(database).upsert([replace(candles[40], volume=2)])
    with pytest.raises(ValueError, match="dataset changed"):
        reproduce_run(database, "binance", child)
