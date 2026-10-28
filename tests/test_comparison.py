from dataclasses import replace
from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.backtest.comparison import load_comparison, comparison_warnings, comparison_chart
from app.backtest.configuration import make_strategy
from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.backtest.runs import BacktestRunRepository
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository


def fixture_runs(path: Path):
    candles = [Candle("binance", "BTC/USDT", "1d", i*TIMEFRAMES_MS["1d"],
                      100+i, 102+i, 99+i, 101+i, 1) for i in range(20)]
    CandleRepository(path).upsert(candles)
    repo = BacktestRunRepository(path)
    runs, results = [], []
    for family in ("sma", "buy-hold"):
        config = BacktestConfig()
        result = BacktestEngine(config).run(candles, make_strategy(family, config, fast=2, slow=3))
        run = repo.save(result, candles, config, "development", "", 2 if family == "sma" else None, 3 if family == "sma" else None)
        runs.append(run)
        results.append(result)
    return candles, runs, results


def test_full_results_round_trip_including_infinite_profit_factor(tmp_path) -> None:
    path = tmp_path / "test.sqlite3"
    _, runs, results = fixture_runs(path)
    repo = BacktestRunRepository(path)
    for run, result in zip(runs, results):
        stored, source = repo.get_result(run.run_key)
        assert stored == result
        assert source == "original"
        assert stored.metrics.profit_factor == float("inf")
    # First saved snapshot wins, even if a later caller offers a different interior point.
    modified = replace(results[0], equity_curve=[results[0].equity_curve[0],
                                                replace(results[0].equity_curve[1], equity=123),
                                                *results[0].equity_curve[2:]])
    repo.save_reproduced_result(runs[0].run_key, modified)
    assert repo.get_result(runs[0].run_key)[0] == results[0]


def test_same_period_picker_excludes_other_dates_and_same_strategy_version(tmp_path, monkeypatch) -> None:
    path = tmp_path / "test.sqlite3"
    candles, runs, _ = fixture_runs(path)
    repo = BacktestRunRepository(path)
    config = BacktestConfig()
    short = BacktestEngine(config).run(candles[:10], make_strategy("buy-hold", config))
    wrong_period = repo.save(short, candles[:10], config, "development", "", None, None)
    different_cost = replace(config, fee_bps=20)
    same_version = BacktestEngine(different_cost).run(candles, make_strategy("sma", different_cost, fast=2, slow=3))
    same = repo.save(same_version, candles, different_cost, "development", "", 2, 3)
    assert [run.run_key for run in repo.list_matching_period(runs[0])] == [runs[1].run_key]
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    client = TestClient(app)
    response = client.get(f"/backtests/results/{runs[0].run_key}/matches")
    assert response.status_code == 200
    assert "1970-01-01 → 1970-01-21" in response.text
    assert "與基準比較" in response.text
    assert runs[1].run_key in response.text
    assert wrong_period.run_key not in response.text
    assert same.run_key not in response.text
    dashboard = client.get("/").text
    assert "回測區間（UTC）" in dashboard
    assert "找同區間比較" in dashboard
    assert client.get("/backtests/results/missing/matches").status_code == 404


def test_interval_first_workspace_lists_only_exact_period_results(tmp_path, monkeypatch) -> None:
    path = tmp_path / "test.sqlite3"
    candles, runs, _ = fixture_runs(path)
    config = BacktestConfig()
    result = BacktestEngine(config).run(candles[:10], make_strategy("buy-hold", config))
    short = BacktestRunRepository(path).save(result, candles[:10], config, "development", "", None, None)
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    client = TestClient(app)
    full_period = f"0:{20*TIMEFRAMES_MS['1d']}"
    short_period = f"0:{10*TIMEFRAMES_MS['1d']}"
    response = client.get("/backtests/select", params=dict(symbol="BTC/USDT", timeframe="1d",
                                                         period=full_period))
    assert response.status_code == 200
    assert "同區間，策略比較" in response.text
    assert 'name="period_a"' not in response.text and 'name="period_b"' not in response.text
    assert {item["run"].run_key for item in response.context["experiments"]} == {run.run_key for run in runs}
    shorter = client.get("/backtests/select", params=dict(symbol="BTC/USDT", timeframe="1d", period=short_period))
    assert [item["run"].run_key for item in shorter.context["experiments"]] == [short.run_key]
    comparison = client.get("/backtests/compare", params=dict(left_run_key=runs[0].run_key, right_run_key=runs[1].run_key))
    assert comparison.status_code == 200
    duplicate = client.get("/backtests/compare", params=dict(left_run_key=runs[0].run_key, right_run_key=runs[0].run_key))
    assert duplicate.status_code == 400
    assert len(BacktestRunRepository(path).list_recent()) == 3


def test_interval_workspace_handles_missing_market_and_stale_interval(tmp_path, monkeypatch) -> None:
    path = tmp_path / "test.sqlite3"
    fixture_runs(path)
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    client = TestClient(app)
    empty = client.get("/backtests/select", params=dict(symbol="ETH/USDT", timeframe="1d"))
    assert empty.status_code == 200
    assert "尚無已保存的回測" in empty.text
    stale = client.get("/backtests/select", params=dict(symbol="BTC/USDT", timeframe="1d", period="1:2"))
    assert stale.status_code == 200
    assert "請重新選擇區間" in stale.text
    assert stale.context["experiments"] == []


def test_single_period_can_compare_v1_and_v3_without_selecting_v2(tmp_path, monkeypatch) -> None:
    path = tmp_path / "test.sqlite3"
    candles, runs, _ = fixture_runs(path)
    repo = BacktestRunRepository(path)
    config = BacktestConfig()
    versions = [runs[0]]
    for slow in (4, 5):
        result = BacktestEngine(config).run(candles, make_strategy("sma", config, fast=2, slow=slow))
        versions.append(repo.save(result, candles, config, "development", "", 2, slow,
                                  base_run_key=versions[-1].run_key))
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    client = TestClient(app)
    page = client.get("/backtests/select", params=dict(symbol="BTC/USDT", timeframe="1d",
                                                     period=f"0:{20*TIMEFRAMES_MS['1d']}"))
    assert len(page.context["experiments"]) == 4
    assert "V3" in page.text
    assert 'type="radio"' not in page.text
    comparison = client.get("/backtests/compare", params=[("run_keys", versions[0].run_key),
                                                        ("run_keys", versions[2].run_key)])
    assert comparison.status_code == 200
    assert [entry.version for entry in comparison.context["entries"]] == [1, 3]
    assert versions[1].run_key not in comparison.text
    assert len(repo.list_recent()) == 4


def test_single_result_page_uses_snapshot_without_rerunning_or_creating_runs(tmp_path, monkeypatch) -> None:
    path = tmp_path / "test.sqlite3"
    _, runs, _ = fixture_runs(path)
    CandleRepository(path).delete_dataset("binance", "BTC/USDT", "1d")
    monkeypatch.setenv("QUANT_DB_PATH", str(path))

    def unexpected_reproduction(*args, **kwargs):
        raise AssertionError("saved result must not rerun the engine")

    monkeypatch.setattr("app.backtest.comparison.reproduce_run", unexpected_reproduction)
    client = TestClient(app)
    for _ in range(2):
        response = client.get(f"/backtests/results/{runs[0].run_key}")
        assert response.status_code == 200
        assert "已保存的回測結果" in response.text
        assert "原始快照" in response.text
        assert "資產曲線" in response.text
        assert "交易紀錄" in response.text
        assert "已新增" not in response.text
    assert len(BacktestRunRepository(path).list_recent()) == 2
    assert client.get("/backtests/results/missing").status_code == 404
    assert f'/backtests/results/{runs[0].run_key}' in client.get("/").text


def test_single_legacy_result_can_backfill_or_show_honest_missing_state(tmp_path, monkeypatch) -> None:
    path = tmp_path / "test.sqlite3"
    candles, runs, _ = fixture_runs(path)
    with sqlite3.connect(path) as connection:
        connection.execute("DELETE FROM backtest_results")
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    client = TestClient(app)
    recovered = client.get(f"/backtests/results/{runs[0].run_key}")
    assert recovered.status_code == 200
    assert "重現後補存" in recovered.text
    CandleRepository(path).upsert([replace(candles[5], volume=999)])
    missing = client.get(f"/backtests/results/{runs[1].run_key}")
    assert missing.status_code == 200
    assert "無法還原的資產曲線與交易明細不會補造" in missing.text
    assert "最終資產" in missing.text


def test_comparison_survives_deletion_of_underlying_candles(tmp_path, monkeypatch) -> None:
    path = tmp_path / "test.sqlite3"
    _, runs, results = fixture_runs(path)
    CandleRepository(path).delete_dataset("binance", "BTC/USDT", "1d")
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    response = TestClient(app).get("/backtests/compare", params=[("run_keys", run.run_key) for run in runs])
    assert response.status_code == 200
    assert "淨盈虧（USDT）" in response.text
    assert "原始結果快照" in response.text
    assert 'comparison-line-0' in response.text and 'comparison-line-1' in response.text
    assert "∞" in response.text
    assert comparison_warnings(load_comparison(path, "binance", [run.run_key for run in runs])) == []


def test_legacy_snapshots_are_backfilled_only_after_exact_reproduction(tmp_path) -> None:
    path = tmp_path / "test.sqlite3"
    _, runs, results = fixture_runs(path)
    with sqlite3.connect(path) as connection:
        connection.execute("DELETE FROM backtest_results")
    entries = load_comparison(path, "binance", [run.run_key for run in runs])
    assert [entry.source for entry in entries] == ["reproduced", "reproduced"]
    assert entries[0].result == results[0]
    assert BacktestRunRepository(path).get_run(runs[0].run_key) == runs[0]
    assert len(BacktestRunRepository(path).list_recent()) == 2


def test_changed_legacy_data_reports_missing_curve_without_fabricating_results(tmp_path, monkeypatch) -> None:
    path = tmp_path / "test.sqlite3"
    candles, runs, _ = fixture_runs(path)
    with sqlite3.connect(path) as connection:
        connection.execute("DELETE FROM backtest_results WHERE run_key=?", (runs[0].run_key,))
    CandleRepository(path).upsert([replace(candles[5], volume=999)])
    entries = load_comparison(path, "binance", [run.run_key for run in runs])
    assert entries[0].result is None
    assert entries[0].error
    assert entries[1].source == "original"
    assert BacktestRunRepository(path).get_result(runs[0].run_key) is None
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    response = TestClient(app).get("/backtests/compare", params=[("run_keys", run.run_key) for run in runs])
    assert response.status_code == 200
    assert "舊紀錄無法精確重現" in response.text


@pytest.mark.parametrize("keys", [[], ["a"*64], ["a"*64, "a"*64], ["a"*64, "b"*64], ["a"*64, "b"*64, "c"*64]])
def test_comparison_rejects_invalid_selection(tmp_path, monkeypatch, keys) -> None:
    monkeypatch.setenv("QUANT_DB_PATH", str(tmp_path / "empty.sqlite3"))
    response = TestClient(app).get("/backtests/compare", params=[("run_keys", key) for key in keys])
    assert response.status_code == 400


def test_mismatches_are_visible_and_curves_use_actual_timestamps(tmp_path) -> None:
    path = tmp_path / "test.sqlite3"
    _, runs, _ = fixture_runs(path)
    entries = load_comparison(path, "binance", [run.run_key for run in runs])
    different = replace(entries[1], run=replace(entries[1].run, initial_cash=20_000, fee_bps=20,
                                               since_ms=TIMEFRAMES_MS["1d"], stop_loss_pct=0.1),
                        result=replace(entries[1].result, equity_curve=entries[1].result.equity_curve[2:]))
    warnings = comparison_warnings([entries[0], different])
    assert any("日期不同" in warning for warning in warnings)
    assert any("初始資金不同" in warning for warning in warnings)
    assert any("手續費率" in warning for warning in warnings)
    assert any("止盈止損" in warning for warning in warnings)
    chart = comparison_chart([entries[0], different])
    starts = [float(series["points"].split()[0].split(",")[0]) for series in chart["series"]]
    assert starts[1] > starts[0]
    indexed = comparison_chart(entries, "indexed")
    assert indexed["high"] < chart["high"]


def test_entered_dates_query_exact_period_and_empty_range(tmp_path, monkeypatch) -> None:
    path = tmp_path / "dates.sqlite3"
    fixture_runs(path)
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    client = TestClient(app)
    response = client.get("/backtests/select", params=dict(timeframe="1d", since="1970-01-01", until="1970-01-21"))
    assert response.status_code == 200
    assert len(response.context["experiments"]) == 2
    assert 'type="date" name="since"' in response.text
    assert '<select name="period">' not in response.text
    empty = client.get("/backtests/select", params=dict(timeframe="1d", since="2026-07-01", until="2026-08-30"))
    assert empty.context["experiments"] == []
    assert "沒有已保存的回測" in empty.text
    invalid = client.get("/backtests/select", params=dict(since="2026-08-30", until="2026-07-01"))
    assert "結束日期必須晚於開始日期" in invalid.text


def test_pair_review_preserves_evidence_and_agent_judgment(tmp_path, monkeypatch) -> None:
    from app.backtest.reviews import ComparisonReviewRepository
    path = tmp_path / "review.sqlite3"
    _, runs, _ = fixture_runs(path)
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    client = TestClient(app)
    keys = [run.run_key for run in runs]
    response = client.post("/comparison-reviews", data={"run_keys": keys, "objective": "V1 是否更好？"})
    assert response.status_code == 200
    assert "等待 AI 判斷" in response.text
    repo = ComparisonReviewRepository(path)
    item = repo.list_requests()[0]
    assert item["objective"] == "V1 是否更好？"
    assert len(item["evidence"]["entries"]) == 2
    assert item["evidence"]["entries"][0]["metrics"] is not None
    assert repo.enqueue("binance", keys[::-1])["request_id"] == item["request_id"]
    assert len(repo.list_requests()) == 1
    repo.finish(item["request_id"], "completed", "舊版收益較高；單一期間不足以證明整體優勢。")
    assert "舊版收益較高" in client.get("/comparison-reviews").text
    with pytest.raises(ValueError):
        repo.finish(item["request_id"], "completed", "不能覆寫")
    assert len(BacktestRunRepository(path).list_recent()) == 2
    assert client.post("/comparison-reviews", data={"run_keys": [keys[0], keys[0]]}).status_code == 400
