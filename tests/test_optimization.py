from app.backtest.optimization import OptimizationRequestRepository


RUN_KEY = "a" * 64
CANDIDATE_KEY = "b" * 64


def test_optimization_queue_records_lifecycle(tmp_path) -> None:
    repository = OptimizationRequestRepository(tmp_path / "market.sqlite3")
    request = repository.enqueue(RUN_KEY, "降低最大回撤")
    duplicate = repository.enqueue(RUN_KEY, "不應建立第二筆")

    assert duplicate.request_id == request.request_id
    assert repository.list_requests("pending") == [duplicate]

    assert repository.complete(
        request.request_id,
        candidate_run_key=CANDIDATE_KEY,
        decision="reduce_risk",
        changes={"leverage": 2},
        summary="槓桿由 3x 降為 2x",
        validation_plan="使用 Validation 區間確認",
    )
    completed = repository.get(request.request_id)
    assert completed is not None
    assert completed.status == "completed"
    assert completed.candidate_run_key == CANDIDATE_KEY
    assert completed.changes == {"leverage": 2}
    assert not repository.complete(
        request.request_id,
        candidate_run_key=CANDIDATE_KEY,
        decision="duplicate",
        changes={},
        summary="duplicate",
        validation_plan="duplicate",
    )
