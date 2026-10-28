from dataclasses import replace
import json

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.backtest.configuration import make_strategy
from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.backtest.optimization import OptimizationRequestRepository
from app.backtest.runs import BacktestRunRepository
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository
from scripts.optimize_backtest import main


DAY = TIMEFRAMES_MS["1d"]


def seed(path):
    candles = [Candle("binance", "BTC/USDT", "1d", i*DAY,
                      100+i%7, 102+i%7, 98+i%7, 100+i%7, 1) for i in range(90)]
    CandleRepository(path).upsert(candles)
    return candles


def save_period(path, candles, stage="development"):
    config = BacktestConfig(stop_loss_pct=0.05, take_profit_pct=0.1)
    result = BacktestEngine(config).run(candles, make_strategy("sma", config, fast=2, slow=3))
    return BacktestRunRepository(path).save(result, candles, config, stage, "", 2, 3)


def test_saved_version_accepts_new_dates_and_ignores_parameter_tampering(tmp_path, monkeypatch) -> None:
    path = tmp_path / "test.sqlite3"
    candles = seed(path)
    base = save_period(path, candles[:30])
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    client = TestClient(app)
    response = client.get("/backtests/run", params=dict(
        strategy_key=base.strategy_key, symbol="BTC/USDT", timeframe="1d", strategy="sma",
        since="1970-02-01", until="1970-03-01", fast=10, slow=20,
        risk_per_trade_pct=0.1, research_plan_id="old-stale-selection", stage="validation",
    ))
    assert response.status_code == 200
    repo = BacktestRunRepository(path)
    assert len(repo.list_strategy_versions()) == 1
    runs = repo.list_runs_for_strategy(base.strategy_key)
    assert len(runs) == 2
    assert all(run.fast_period == 2 and run.slow_period == 3 for run in runs)
    assert all(run.policy_json == "{}" for run in runs)
    assert "research-plan-select" not in client.get("/").text


def test_version_backtests_use_separate_page_and_only_selected_version(tmp_path, monkeypatch) -> None:
    path = tmp_path / "test.sqlite3"
    candles = seed(path)
    first = save_period(path, candles[:30])
    save_period(path, candles[30:60])
    config = BacktestConfig(risk_per_trade=0.005, stop_loss_pct=0.05)
    result = BacktestEngine(config).run(candles, make_strategy("sma", config, fast=2, slow=3))
    other = BacktestRunRepository(path).save(result, candles, config, "development", "", 2, 3)
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    client = TestClient(app)
    dashboard = client.get("/")
    assert f'/strategies/{first.strategy_key}/backtests' in dashboard.text
    assert "<details><summary>查看" not in dashboard.text
    response = client.get(f"/strategies/{first.strategy_key}/backtests")
    assert response.status_code == 200
    assert "此版本的 2 筆回測" in response.text
    assert "返回策略列表" in response.text
    assert other.strategy_key not in response.text
    assert client.get("/strategies/unknown/backtests").status_code == 404


def test_queue_deduplicates_by_version_and_optimizer_compares_every_period(tmp_path, monkeypatch, capsys) -> None:
    path = tmp_path / "test.sqlite3"
    candles = seed(path)
    first = save_period(path, candles[:30])
    second = save_period(path, candles[30:60], "validation")
    queue = OptimizationRequestRepository(path)
    request = queue.enqueue(first.run_key, "減少無效交易")
    duplicate = queue.enqueue(second.run_key)
    assert duplicate.request_id == request.request_id
    assert set(duplicate.evidence_run_keys) == {first.run_key, second.run_key}
    third = save_period(path, candles[60:])
    monkeypatch.setattr("sys.argv", ["optimizer", "--db", str(path), "optimize-request",
                                    "--request-id", str(request.request_id),
                                    "--changes-json", '{"fast":3,"slow":5}',
                                    "--note", "參考各期間無效交易，測試較慢均線；不修改倉位與出場"])
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "candidate_saved"
    completed = queue.get(request.request_id)
    assert completed.status == "completed"
    assert set(completed.evidence_run_keys) == {first.run_key, second.run_key, third.run_key}
    comparisons = json.loads(completed.comparisons_json)
    assert len(comparisons) == 3
    repo = BacktestRunRepository(path)
    versions = repo.list_strategy_versions()
    assert len(versions) == 2
    child = next(version for version in versions if version.strategy_key != first.strategy_key)
    assert child.previous_strategy_key == first.strategy_key
    assert len(repo.list_runs_for_strategy(child.strategy_key)) == 3
    assert repo.get_run(first.run_key) == first
    assert any(row["source_stage"] == "validation" and row["source_used_for_tuning"] for row in comparisons)
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    response = TestClient(app).get("/strategy-optimizations")
    assert response.status_code == 200
    assert "查看各區間新舊比較" in response.text


def test_bad_evidence_fails_entire_request_instead_of_omitting_period(tmp_path, monkeypatch) -> None:
    path = tmp_path / "test.sqlite3"
    candles = seed(path)
    first = save_period(path, candles[:30])
    second = save_period(path, candles[30:60])
    queue = OptimizationRequestRepository(path)
    request = queue.enqueue_version(first.strategy_key)
    CandleRepository(path).upsert([replace(candles[40], volume=999)])
    monkeypatch.setattr("sys.argv", ["optimizer", "--db", str(path), "optimize-request",
                                    "--request-id", str(request.request_id)])
    with pytest.raises(SystemExit):
        main()
    assert queue.get(request.request_id).status == "failed"
    assert len(BacktestRunRepository(path).list_strategy_versions()) == 1


def test_stop_reentry_candidate_survives_optimizer_replay_and_locked_dashboard(tmp_path, monkeypatch, capsys) -> None:
    from app.backtest.reproduction import reproduce_run
    path = tmp_path / "reentry.sqlite3"
    candles = seed(path)
    base = save_period(path, candles)
    queue = OptimizationRequestRepository(path)
    task = queue.enqueue(base.run_key)
    monkeypatch.setattr("sys.argv", ["optimize", "--db", str(path), "optimize-request", "--request-id", str(task.request_id),
                                     "--changes-json", '{"stop_reentry_mode":"signal_reset"}', "--note", "測試止損後重新進場限制"])
    main()
    payload = json.loads(capsys.readouterr().out)
    repo = BacktestRunRepository(path)
    child = repo.get_run(payload["candidate"]["run_key"])
    assert json.loads(child.policy_json)["stop_reentry_mode"] == "signal_reset"
    assert repo.get_result(child.run_key)[0] == reproduce_run(path, "binance", child)[2]
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    response = TestClient(app).get("/backtests/run", params=dict(strategy_key=child.strategy_key, symbol="BTC/USDT", timeframe="1d", strategy="sma",
                                                               since="1970-02-01", until="1970-03-01", stop_reentry_mode="immediate"))
    assert response.status_code == 200
    assert response.context["values"]["stop_reentry_mode"] == "signal_reset"
    assert response.context["saved_run"].strategy_key == child.strategy_key


def test_buffer_candidate_round_trip_and_locked_dashboard(tmp_path, monkeypatch, capsys) -> None:
    from app.backtest.reproduction import reproduce_run
    path = tmp_path / "buffer.sqlite3"
    candles = seed(path)
    base = save_period(path, candles)
    task = OptimizationRequestRepository(path).enqueue(base.run_key)
    monkeypatch.setattr("sys.argv", ["optimize", "--db", str(path), "optimize-request", "--request-id", str(task.request_id),
                                     "--changes-json", '{"trend_entry_buffer_pct":1}', "--note", "只測固定1%門檻"])
    main()
    payload = json.loads(capsys.readouterr().out)
    repo = BacktestRunRepository(path)
    child = repo.get_run(payload["candidate"]["run_key"])
    assert json.loads(child.policy_json)["trend_entry_buffer"] == 0.01
    assert repo.get_result(child.run_key)[0] == reproduce_run(path, "binance", child)[2]
    assert repo.get_run(base.run_key).policy_json == "{}"
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    response = TestClient(app).get("/backtests/run", params=dict(strategy_key=child.strategy_key, symbol="BTC/USDT", timeframe="1d", strategy="sma",
                                                               since="1970-02-01", until="1970-03-01", trend_entry_buffer_pct=0))
    assert response.status_code == 200
    assert response.context["values"]["trend_entry_buffer_pct"] == 1
    assert response.context["saved_run"].strategy_key == child.strategy_key


def test_trailing_candidate_round_trip_and_locked_dashboard(tmp_path, monkeypatch, capsys) -> None:
    from app.backtest.reproduction import reproduce_run
    path = tmp_path / "trailing.sqlite3"
    candles = seed(path)
    base = save_period(path, candles)
    task = OptimizationRequestRepository(path).enqueue(base.run_key)
    monkeypatch.setattr("sys.argv", ["optimize", "--db", str(path), "optimize-request", "--request-id", str(task.request_id),
                                     "--changes-json", '{"trailing_activation_pct":5,"trailing_distance_pct":5}', "--note", "只測5%啟動和5%收盤追蹤"])
    main()
    payload = json.loads(capsys.readouterr().out)
    repo = BacktestRunRepository(path)
    child = repo.get_run(payload["candidate"]["run_key"])
    policy = json.loads(child.policy_json)
    assert policy["trailing_activation"] == policy["trailing_distance"] == 0.05
    assert repo.get_result(child.run_key)[0] == reproduce_run(path, "binance", child)[2]
    assert repo.get_run(base.run_key).policy_json == "{}"
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    response = TestClient(app).get("/backtests/run", params=dict(strategy_key=child.strategy_key, symbol="BTC/USDT", timeframe="1d", strategy="sma",
                                                               since="1970-02-01", until="1970-03-01", trailing_activation_pct=0, trailing_distance_pct=0))
    assert response.status_code == 200
    assert response.context["values"]["trailing_activation_pct"] == 5
    assert response.context["values"]["trailing_distance_pct"] == 5
    assert response.context["saved_run"].strategy_key == child.strategy_key


@pytest.mark.parametrize("reentry", ["exit_high_breakout", "pullback_reclaim"])
def test_trailing_breakout_candidate_replays_and_dashboard_cannot_drop_rule(tmp_path, monkeypatch, capsys, reentry) -> None:
    from app.backtest.reproduction import reproduce_run
    path = tmp_path / "breakout.sqlite3"
    candles = seed(path)
    base = save_period(path, candles)
    task = OptimizationRequestRepository(path).enqueue(base.run_key)
    monkeypatch.setattr("sys.argv", ["optimize", "--db", str(path), "optimize-request", "--request-id", str(task.request_id),
        "--changes-json", json.dumps(dict(trailing_activation_pct=5,trailing_distance_pct=5,trailing_reentry_mode=reentry)),
        "--note", "固定退出高點突破後再進場"])
    main()
    payload = json.loads(capsys.readouterr().out)
    repo = BacktestRunRepository(path)
    child = repo.get_run(payload["candidate"]["run_key"])
    assert json.loads(child.policy_json)["trailing_reentry_mode"]==reentry
    assert repo.get_result(child.run_key)[0]==reproduce_run(path,"binance",child)[2]
    assert repo.get_run(base.run_key).policy_json=="{}"
    monkeypatch.setenv("QUANT_DB_PATH",str(path))
    response=TestClient(app).get("/backtests/run",params=dict(strategy_key=child.strategy_key,symbol="BTC/USDT",timeframe="1d",strategy="sma",
        since="1970-02-01",until="1970-03-01",trailing_reentry_mode="inherit"))
    assert response.status_code==200
    assert response.context["values"]["trailing_reentry_mode"]==reentry
    assert response.context["saved_run"].strategy_key==child.strategy_key


def test_regime_candidate_replays_and_dashboard_cannot_drop_risk_rule(tmp_path, monkeypatch, capsys):
    from app.backtest.reproduction import reproduce_run
    path = tmp_path / "regime.sqlite3"
    candles = seed(path)
    base = save_period(path, candles)
    task = OptimizationRequestRepository(path).enqueue(base.run_key)
    monkeypatch.setattr("sys.argv", ["optimize", "--db", str(path), "optimize-request", "--request-id", str(task.request_id),
        "--changes-json", '{"risk_regime":"slow_slope","risk_per_trade_pct":0.5}',
        "--note", "Only test reduced risk when the completed slow SMA slope is nonpositive"])
    main()
    payload = json.loads(capsys.readouterr().out)
    repo = BacktestRunRepository(path)
    child = repo.get_run(payload["candidate"]["run_key"])
    assert json.loads(child.policy_json)["risk_regime"] == "slow_slope"
    assert repo.get_result(child.run_key)[0] == reproduce_run(path, "binance", child)[2]
    assert repo.get_run(base.run_key).policy_json == "{}"
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    response = TestClient(app).get("/backtests/run", params=dict(
        strategy_key=child.strategy_key, symbol="BTC/USDT", timeframe="1d", strategy="sma",
        since="1970-02-01", until="1970-03-01", risk_regime="fixed"))
    assert response.status_code == 200
    assert response.context["values"]["risk_regime"] == "slow_slope"
    assert response.context["saved_run"].strategy_key == child.strategy_key
