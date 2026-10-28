from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.backtest.models import BacktestConfig
from app.backtest.engine import BacktestEngine
from app.backtest.runs import BacktestRunRepository
from app.backtest.research import ResearchPlanRepository
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository
from app.strategies.buy_and_hold import BuyAndHoldStrategy


DAY = TIMEFRAMES_MS["1d"]


def seed(path: Path) -> None:
    CandleRepository(path).upsert([
        Candle("binance", "BTC/USDT", "1d", i*DAY, 100+i, 100+i, 100+i, 100+i, 1)
        for i in range(12)
    ])


def test_plan_rejects_overlapping_periods_and_invalid_bounds(tmp_path) -> None:
    repo = ResearchPlanRepository(tmp_path / "test.sqlite3")
    with pytest.raises(ValueError, match="重疊"):
        repo.create("bad", 0, 3*DAY, 2*DAY, 5*DAY, 6*DAY, 8*DAY)
    with pytest.raises(ValueError, match="日界線"):
        repo.create("bad", 1, 3*DAY, 3*DAY, 5*DAY, 6*DAY, 8*DAY)
    plan = repo.create("fixed", 0, 3*DAY, 3*DAY, 6*DAY, 6*DAY, 9*DAY)
    assert repo.create("fixed", 0, 3*DAY, 3*DAY, 6*DAY, 6*DAY, 9*DAY) == plan


def test_holdout_is_consumed_once_atomically_and_cannot_be_relabelled(tmp_path, monkeypatch) -> None:
    database = tmp_path / "test.sqlite3"
    seed(database)
    monkeypatch.setenv("QUANT_DB_PATH", str(database))
    repo = ResearchPlanRepository(database)
    plan = repo.create("locked", 0, 3*DAY, 3*DAY, 6*DAY, 6*DAY, 9*DAY)
    client = TestClient(app)
    params = dict(symbol="BTC/USDT", timeframe="1d", strategy="buy-hold",
                  since="1970-01-07", until="1970-01-10", stage="out_of_sample",
                  research_plan_id=plan.plan_id)
    assert client.get("/backtests/run", params={**params, "until": "1970-01-09"}).status_code == 422
    assert repo.list_plans()[0].holdout_used == 0
    response = client.get("/backtests/run", params=params)
    assert response.status_code == 200
    assert "載入下一版候選設定" not in response.text
    assert repo.list_plans()[0].holdout_used == 1
    assert client.get("/backtests/run", params=params).status_code == 422
    with pytest.raises(ValueError, match="已查看"):
        repo.create("renamed", 0, 3*DAY, 3*DAY, 6*DAY, 6*DAY, 9*DAY)
    assert len(BacktestRunRepository(database).list_recent()) == 1


def test_holdout_is_invalidated_by_later_exploratory_run(tmp_path) -> None:
    database = tmp_path / "test.sqlite3"
    seed(database)
    repo = ResearchPlanRepository(database)
    plan = repo.create("locked", 0, 3*DAY, 3*DAY, 6*DAY, 6*DAY, 9*DAY)
    candles = CandleRepository(database).list_range("binance", "BTC/USDT", "1d", 6*DAY, 9*DAY)
    config = BacktestConfig()
    result = BacktestEngine(config).run(candles, BuyAndHoldStrategy())
    BacktestRunRepository(database).save(result, candles, config, "development", "observed", None, None)
    with pytest.raises(ValueError, match="已查看"):
        repo.validate(plan.plan_id, "out_of_sample", 6*DAY, 9*DAY)


def test_failed_holdout_save_does_not_consume_period(tmp_path) -> None:
    database = tmp_path / "test.sqlite3"
    seed(database)
    repo = ResearchPlanRepository(database)
    plan = repo.create("locked", 0, 3*DAY, 3*DAY, 6*DAY, 6*DAY, 9*DAY)
    candles = CandleRepository(database).list_range("binance", "BTC/USDT", "1d", 6*DAY, 9*DAY)
    config = BacktestConfig()
    result = BacktestEngine(config).run(candles, BuyAndHoldStrategy())
    with pytest.raises(ValueError, match="base"):
        BacktestRunRepository(database).save(result, candles, config, "out_of_sample", "", None, None,
                                             base_run_key="missing", research_plan_id=plan.plan_id)
    assert repo.list_plans()[0].holdout_used == 0
