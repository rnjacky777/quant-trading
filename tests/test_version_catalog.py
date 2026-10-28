from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.backtest.catalog import VersionCatalogRepository
from app.backtest.configuration import make_strategy
from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.backtest.optimization import OptimizationRequestRepository
from app.backtest.runs import BacktestRunRepository
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository


def save_version(path: Path, fast: int = 2, symbol: str = "BTC/USDT"):
    candles = [Candle("binance", symbol, "1d", i*TIMEFRAMES_MS["1d"],
                      100+i, 102+i, 99+i, 101+i, 1) for i in range(30)]
    CandleRepository(path).upsert(candles)
    config = BacktestConfig()
    result = BacktestEngine(config).run(candles, make_strategy("sma", config, fast=fast, slow=fast+2))
    return BacktestRunRepository(path).save(result, candles, config, "development", "", fast, fast+2)


def test_catalog_focus_is_per_series_and_never_changes_evidence(tmp_path) -> None:
    path = tmp_path / "catalog.sqlite3"
    first, second, other = save_version(path), save_version(path, 3), save_version(path, 2, "ETH/USDT")
    runs = BacktestRunRepository(path)
    versions_before = runs.list_strategy_versions()
    snapshots_before = {run.run_key: runs.get_result(run.run_key) for run in (first, second, other)}
    catalog = VersionCatalogRepository(path)
    assert catalog.categories(versions_before)[first.strategy_key] == "reference"
    assert catalog.categories(versions_before)[second.strategy_key] == "candidate"
    catalog.set_category(first.strategy_key, "focus")
    catalog.set_category(other.strategy_key, "focus")
    catalog.set_category(second.strategy_key, "focus")
    saved = VersionCatalogRepository(path).categories(versions_before)
    assert saved[first.strategy_key] == "reference"
    assert saved[second.strategy_key] == saved[other.strategy_key] == "focus"
    assert runs.list_strategy_versions() == versions_before
    assert {key: runs.get_result(key) for key in snapshots_before} == snapshots_before
    assert len(runs.list_recent()) == 3
    with pytest.raises(ValueError):
        catalog.set_category(second.strategy_key, "invalid")
    with pytest.raises(ValueError):
        catalog.set_category("missing", "archived")


def test_archived_version_remains_accessible_and_pending_tasks_are_visible(tmp_path, monkeypatch) -> None:
    path = tmp_path / "archive.sqlite3"
    run = save_version(path)
    task = OptimizationRequestRepository(path).enqueue(run.run_key)
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    client = TestClient(app)
    response = client.post(f"/strategies/{run.strategy_key}/classification", data={"category": "archived"}, follow_redirects=False)
    assert response.status_code == 303
    page = client.get("/")
    group = page.context["version_groups"][0]
    assert len(group["archived"]) == 1 and group["archived_pending"]
    assert "有等待 AI 優化任務" in page.text
    assert "封存仍保留所有回測與比較" in page.text
    assert client.get(f"/backtests/results/{run.run_key}").status_code == 200
    assert client.get(f"/strategies/{run.strategy_key}/backtests").status_code == 200
    assert OptimizationRequestRepository(path).get(task.request_id).status == "pending"
    assert client.post(f"/strategies/{run.strategy_key}/classification", data={"category": "reference"}).status_code == 200
    assert client.post("/strategies/missing/classification", data={"category": "focus"}).status_code == 404
    assert client.post(f"/strategies/{run.strategy_key}/classification", data={"category": "invalid"}).status_code == 422


def test_new_versions_are_candidates_and_do_not_replace_focus(tmp_path, monkeypatch) -> None:
    path = tmp_path / "new.sqlite3"
    run = save_version(path)
    catalog = VersionCatalogRepository(path)
    catalog.set_category(run.strategy_key, "focus")
    candidate = save_version(path, 3)
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    page = TestClient(app).get("/")
    group = page.context["version_groups"][0]
    assert [item["version"].strategy_key for item in group["primary"]] == [run.strategy_key]
    assert [item["version"].strategy_key for item in group["candidate"]] == [candidate.strategy_key]
    assert not group["candidate_pending"]
    assert 'id="show-archived-versions"' in page.text
    assert 'data-default-open="false"' in page.text
