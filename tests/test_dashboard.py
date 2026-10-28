from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import app
from app.backtest.runs import BacktestRunRepository
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository


def _seed(path: Path) -> None:
    step = TIMEFRAMES_MS["1d"]
    candles = [
        Candle(
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1d",
            timestamp_ms=index * step,
            open=100 + index,
            high=102 + index,
            low=99 + index,
            close=101 + index,
            volume=10,
        )
        for index in range(90)
    ]
    CandleRepository(path).upsert(candles)


def test_dashboard_lists_coverage_and_runs_backtest(tmp_path, monkeypatch) -> None:
    database = tmp_path / "market.sqlite3"
    _seed(database)
    monkeypatch.setenv("QUANT_DB_PATH", str(database))
    client = TestClient(app)

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert "量化交易研究台" in dashboard.text
    assert "BTC/USDT" in dashboard.text
    assert 'data-persist-key="quant-backtest-form"' in dashboard.text
    assert "/static/dashboard.js?v=28" in dashboard.text
    assert "實際已下載開始" in dashboard.text
    assert "日期是要求回測的範圍" in dashboard.text
    assert "Funding Rate" in dashboard.text
    assert "自動跟隨下方 BACKTEST" in dashboard.text

    result = client.get(
        "/backtests/run",
        params={
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "since": "1970-01-01",
            "until": "1970-04-01",
            "strategy": "sma",
            "fast": 5,
            "slow": 20,
        },
    )
    assert result.status_code == 200
    assert "BACKTEST RESULT" in result.text
    assert "資產曲線" in result.text
    assert "交易紀錄" in result.text
    assert "AI OPTIMIZATION" in result.text
    assert "此版本目前有" in result.text
    assert "止損" in result.text
    assert "槓桿" in result.text
    assert "標記等待 AI 優化" in result.text
    assert "已建立策略版本 V1" in result.text

    recorded = BacktestRunRepository(database).list_recent()
    assert len(recorded) == 1
    assert recorded[0].stop_loss_pct == 0.05
    assert recorded[0].take_profit_pct == 0.10
    assert recorded[0].leverage == 1
    adjustments = BacktestRunRepository(database).list_adjustments()
    assert len(adjustments) == 1
    assert adjustments[0].previous_run_key is None
    assert adjustments[0].version_number == 1
    assert adjustments[0].changes == {}

    original_created_at = recorded[0].created_at_ms
    duplicate = client.get(result.request.url)
    assert duplicate.status_code == 200
    assert "重複設定" in duplicate.text
    assert "沿用 V1" in duplicate.text
    assert "沒有建立新版本" in duplicate.text
    assert len(BacktestRunRepository(database).list_recent()) == 1
    assert len(BacktestRunRepository(database).list_adjustments()) == 1
    assert (
        BacktestRunRepository(database).list_recent()[0].created_at_ms
        == original_created_at
    )

    changed = client.get(
        "/backtests/run",
        params={
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "since": "1970-01-01",
            "until": "1970-04-01",
            "strategy": "sma",
            "fast": 5,
            "slow": 20,
            "risk_per_trade_pct": 0.5,
            "note": "測試風險倉位",
        },
    )
    assert changed.status_code == 200
    adjustments = BacktestRunRepository(database).list_adjustments()
    assert len(adjustments) == 2
    assert adjustments[0].hypothesis == "測試風險倉位"
    assert adjustments[0].version_number == 2
    assert "policy_json" in adjustments[0].changes

    branched = client.get(
        "/backtests/run",
        params={
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "since": "1970-01-01",
            "until": "1970-04-01",
            "strategy": "sma",
            "fast": 5,
            "slow": 20,
            "risk_per_trade_pct": 0.25,
            "note": "從 V1 測試較小風險",
            "base_run_key": recorded[0].run_key,
        },
    )
    assert branched.status_code == 200
    adjustments = BacktestRunRepository(database).list_adjustments()
    assert adjustments[0].version_number == 3
    assert adjustments[0].previous_run_key == recorded[0].run_key
    assert "policy_json" in adjustments[0].changes

    dashboard = client.get("/")
    assert "STRATEGY LIBRARY" in dashboard.text
    assert 'id="backtest-strategy-version"' in dashboard.text
    assert 'data-strategy="sma"' in dashboard.text
    assert 'data-run-key="' in dashboard.text
    assert "V2" in dashboard.text
    assert "基於 V1" in dashboard.text
    assert "測試風險倉位" in dashboard.text
    assert "1.0x" in dashboard.text
    assert "0.50%" in dashboard.text
    assert "標記等待 AI 優化" in dashboard.text
    assert "載入此區間" in dashboard.text
    assert "load_strategy=history" in dashboard.text
    assert 'id="adjustment-filters"' in dashboard.text
    assert 'id="strategy-version-groups"' in dashboard.text
    assert 'id="adjustment-visible-count">3</strong> / 3 個版本' in dashboard.text
    assert 'id="history-filters"' in dashboard.text
    assert 'name="recorded_from"' in dashboard.text
    assert 'name="recorded_until"' in dashboard.text
    assert 'name="strategy"' in dashboard.text
    assert 'name="version"' in dashboard.text
    assert 'data-strategy="sma"' in dashboard.text
    assert 'data-timeframe="1d"' in dashboard.text
    assert 'data-version="3"' in dashboard.text
    assert '<option value="3">V3</option>' in dashboard.text
    assert "顯示 <strong id=\"history-visible-count\">3</strong> / 3 筆紀錄" in dashboard.text

    queued = client.post(
        "/strategy-optimizations/enqueue",
        data={
            "run_key": adjustments[0].run_key,
            "objective": "降低回撤並保留趨勢報酬",
        },
        follow_redirects=False,
    )
    assert queued.status_code == 303
    assert queued.headers["location"].startswith("/strategy-optimizations?")

    optimization_page = client.get("/strategy-optimizations")
    assert optimization_page.status_code == 200
    assert "OPTIMIZATION QUEUE" in optimization_page.text
    assert "降低回撤並保留趨勢報酬" in optimization_page.text
    assert "等待 AI 優化" in optimization_page.text


def test_dashboard_explains_missing_data(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("QUANT_DB_PATH", str(tmp_path / "empty.sqlite3"))
    response = TestClient(app).get(
        "/backtests/run",
        params={
            "symbol": "ETH/USDT",
            "timeframe": "4h",
            "since": "2024-01-01",
            "until": "2024-02-01",
            "strategy": "sma",
        },
    )
    assert response.status_code == 422
    assert "沒有資料" in response.text
    assert "下載這段 K 線" in response.text
    assert 'value="ETH/USDT"' in response.text
    assert 'name="return_to" value="backtest"' in response.text


def test_dashboard_rejects_partial_date_coverage(tmp_path, monkeypatch) -> None:
    database = tmp_path / "partial.sqlite3"
    _seed(database)
    monkeypatch.setenv("QUANT_DB_PATH", str(database))
    response = TestClient(app).get(
        "/backtests/run",
        params={
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "since": "1970-01-01",
            "until": "1970-05-01",
            "strategy": "sma",
        },
    )
    assert response.status_code == 422
    assert "資料不完整" in response.text
    assert "需要 120 根，目前只有 90 根" in response.text


def test_validation_only_version_can_be_marked_without_development_branch(tmp_path, monkeypatch) -> None:
    database = tmp_path / "market.sqlite3"
    _seed(database)
    monkeypatch.setenv("QUANT_DB_PATH", str(database))
    client = TestClient(app)
    result = client.get("/backtests/run", params=dict(
        symbol="BTC/USDT", timeframe="1d", since="1970-01-01", until="1970-04-01",
        strategy="sma", fast=5, slow=20, stage="validation",
    ))
    assert result.status_code == 200
    version = BacktestRunRepository(database).list_strategy_versions()[0]
    dashboard = client.get("/")
    assert "載入 Development 草稿" not in dashboard.text
    assert "research-plan-select" not in dashboard.text
    assert "標記等待 AI 優化" in dashboard.text
    queued = client.post("/strategy-optimizations/enqueue", data={"strategy_key": version.strategy_key})
    assert queued.status_code == 200
    assert "等待 AI 優化" in queued.text


def test_market_period_and_research_stage_do_not_create_strategy_versions(
    tmp_path, monkeypatch
) -> None:
    database = tmp_path / "market.sqlite3"
    _seed(database)
    monkeypatch.setenv("QUANT_DB_PATH", str(database))
    client = TestClient(app)
    common = {
        "symbol": "BTC/USDT",
        "timeframe": "1d",
        "strategy": "sma",
        "fast": 5,
        "slow": 20,
    }

    development = client.get(
        "/backtests/run",
        params={
            **common,
            "since": "1970-01-01",
            "until": "1970-03-01",
            "stage": "development",
        },
    )
    validation = client.get(
        "/backtests/run",
        params={
            **common,
            "since": "1970-03-01",
            "until": "1970-04-01",
            "stage": "validation",
        },
    )

    assert development.status_code == 200
    assert validation.status_code == 200
    repository = BacktestRunRepository(database)
    runs = repository.list_recent()
    versions = repository.list_strategy_versions()
    assert len(runs) == 2
    assert len(versions) == 1
    assert {run.strategy_key for run in runs} == {versions[0].strategy_key}
    assert "已建立策略版本 V1" in development.text
    assert "沿用 V1" in validation.text

    dashboard = client.get("/")
    assert 'id="adjustment-visible-count">1</strong> / 1 個版本' in dashboard.text
    assert 'id="history-visible-count">2</strong> / 2 筆紀錄' in dashboard.text
    assert "2 筆回測" in dashboard.text


def test_dashboard_downloads_and_deletes_a_scoped_dataset(tmp_path, monkeypatch) -> None:
    database = tmp_path / "market.sqlite3"
    monkeypatch.setenv("QUANT_DB_PATH", str(database))

    class FakeProvider:
        exchange_id = "binance"

        def __init__(self, exchange_id: str) -> None:
            assert exchange_id == "binance"

        def fetch_ohlcv(self, symbol, timeframe, since_ms, limit):
            step = TIMEFRAMES_MS[timeframe]
            rows = [
                [index * step, 100, 102, 99, 101, 10]
                for index in range(5)
                if index * step >= since_ms
            ]
            return rows[:limit]

    monkeypatch.setattr(
        "app.api.routes.dashboard.CcxtHistoricalProvider", FakeProvider
    )
    client = TestClient(app)
    downloaded = client.post(
        "/data/download",
        data={
            "symbol": "ETH/USDT",
            "timeframe": "1d",
            "since": "1970-01-01",
            "until": "1970-01-06",
            "return_to": "backtest",
        },
        follow_redirects=False,
    )
    assert downloaded.status_code == 303
    assert downloaded.headers["location"].endswith("#backtest")
    coverage = CandleRepository(database).list_coverage("binance")
    assert coverage[0].symbol == "ETH/USDT"
    assert coverage[0].candle_count == 5

    deleted = client.post(
        "/data/delete",
        data={"symbol": "ETH/USDT", "timeframe": "1d"},
        follow_redirects=False,
    )
    assert deleted.status_code == 303
    assert CandleRepository(database).list_coverage("binance") == []


def test_download_warns_about_source_gap_and_backtest_identifies_it(tmp_path, monkeypatch) -> None:
    database = tmp_path / "market.sqlite3"
    monkeypatch.setenv("QUANT_DB_PATH", str(database))

    class GappedProvider:
        exchange_id = "binance"

        def __init__(self, exchange_id: str) -> None:
            pass

        def fetch_ohlcv(self, symbol, timeframe, since_ms, limit):
            step = TIMEFRAMES_MS[timeframe]
            return [
                [i * step, 100, 102, 99, 101, 10]
                for i in range(6) if i != 3 and i * step >= since_ms
            ][:limit]

    monkeypatch.setattr("app.api.routes.dashboard.CcxtHistoricalProvider", GappedProvider)
    client = TestClient(app)
    response = client.post("/data/download", data={
        "symbol": "BTC/USDT", "timeframe": "4h",
        "since": "1970-01-01", "until": "1970-01-02",
    })
    assert response.status_code == 200
    assert "kind=warning" in str(response.url)
    assert "1970-01-01 12:00 UTC" in response.text
    assert "來源缺漏" in response.text
    result = client.get("/backtests/run", params={
        "symbol": "BTC/USDT", "timeframe": "4h", "strategy": "buy-hold",
        "since": "1970-01-01", "until": "1970-01-02",
    })
    assert result.status_code == 422
    assert "1970-01-01 12:00 UTC" in result.text
    assert CandleRepository(database).list_coverage("binance")[0].candle_count == 5
