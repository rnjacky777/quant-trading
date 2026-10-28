from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from math import isfinite
import os
from pathlib import Path
from typing import Any

from app.backtest.reviews import ComparisonReviewRepository
from app.backtest.advisor import ResearchAdvice, analyze_backtest
from app.backtest.engine import BacktestEngine
from app.backtest.reproduction import reproduce_run, strategy_for_run
from app.backtest.version_optimization import load_version_evidence, analyze_version
from dataclasses import replace
from app.backtest.models import BacktestConfig, BacktestResult
from app.backtest.optimization import OptimizationRequestRepository
from app.backtest.runs import BacktestRun, BacktestRunRepository
from app.data.models import Candle, TIMEFRAMES_MS


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze or create a child version from a saved backtest"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(os.getenv("QUANT_DB_PATH", "data/market.sqlite3")),
    )
    parser.add_argument(
        "--exchange", default=os.getenv("QUANT_EXCHANGE", "binance")
    )
    commands = parser.add_subparsers(dest="command", required=True)
    list_parser = commands.add_parser("list", help="List saved strategy versions")
    list_parser.add_argument("--limit", type=int, default=50)
    commands.add_parser("queue", help="List Dashboard-marked optimization tasks")
    commands.add_parser("lessons", help="Read evidence-linked BTC derivatives research experience")
    for name in ("analyze", "optimize"):
        command = commands.add_parser(name)
        command.add_argument("--run-key", required=True)
        if name == "optimize":
            command.add_argument("--note", default="")
            command.add_argument("--changes-json", default="")
    for name in ("analyze-request", "optimize-request"):
        request_parser = commands.add_parser(name, help="Inspect or optimize one marked strategy version")
        request_parser.add_argument("--request-id", type=int, required=True)
        request_parser.add_argument("--note", default="")
        request_parser.add_argument("--changes-json", default="")
    review_parser = commands.add_parser("analyze-comparison", help="Read frozen pair-review evidence")
    review_parser.add_argument("--request-id", type=int, required=True)
    complete_parser = commands.add_parser("complete-comparison", help="Save agent judgment without creating a version")
    complete_parser.add_argument("--request-id", type=int, required=True)
    complete_parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    if args.command == "lessons":
        from app.backtest.lessons import research_lessons
        try:
            _print_json(research_lessons(args.db.parent))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.error(f"research experience evidence unavailable: {exc}")
        return
    reviews = ComparisonReviewRepository(args.db)
    if args.command in {"analyze-comparison", "complete-comparison"}:
        item = reviews.get(args.request_id)
        if item is None:
            parser.error("comparison review does not exist")
        if args.command == "complete-comparison":
            try:
                reviews.finish(args.request_id, "completed", args.summary)
            except ValueError as exc:
                parser.error(str(exc))
            item = reviews.get(args.request_id)
        _print_json(item)
        return

    repository = BacktestRunRepository(args.db)
    if args.command == "list":
        _print_json(_list_versions(repository, args.limit))
        return

    request_repository = OptimizationRequestRepository(args.db)
    if args.command == "queue":
        _print_json(dict(**_queue_payload(request_repository, repository), comparison_reviews=reviews.list_requests(pending_only=True),
            research_experience=dict(command="python -m scripts.optimize_backtest lessons", scope="BTC perpetual research", required_before_new_hypothesis=True)))
        return

    request = None
    if args.command in {"optimize-request", "analyze-request"}:
        request = request_repository.get(args.request_id)
        if request is None:
            parser.error("optimization request does not exist")
        if request.status != "pending":
            parser.error(f"optimization request is already {request.status}")
        selected_run_key = request.base_run_key
    else:
        selected_run_key = args.run_key

    run = repository.get_run(selected_run_key)
    if run is None:
        parser.error("run_key does not exist")
    if args.command == "optimize":
        request = request_repository.enqueue(run.run_key, args.note)
        if request.base_run_key != run.run_key:
            parser.error("this version already has a pending request; use optimize-request")
    if request is not None:
        request = request_repository.enqueue(request.base_run_key, request.objective)
    try:
        evidence = load_version_evidence(
            args.db, args.exchange, run,
            request.evidence_run_keys if request is not None else None,
        )
        selected = next(item for item in evidence if item.run.run_key == run.run_key)
        advice = analyze_version(evidence)
        evidence_summary = [dict(
            **_run_summary(repository, item.run), metrics=asdict(item.result.metrics),
            used_for_tuning=True,
        ) for item in evidence]
        if args.command in {"analyze", "analyze-request"}:
            payload = _analysis_payload(repository, run, selected.result, advice)
            payload["evidence"] = evidence_summary
            _print_json(payload)
            return
        if args.changes_json:
            changes = json.loads(args.changes_json)
            if not isinstance(changes, dict) or not changes:
                raise ValueError("changes-json 必須是非空物件")
            groups = [set(changes) & fields for fields in (
                {"intraday_strong_close", "intraday_min_atr_pct", "intraday_entry", "higher_timeframe_filter", "fast", "slow", "lookback", "momentum_threshold", "entry_deviation", "trend_entry_buffer_pct"},
                {"max_holding_bars", "stop_loss_pct", "take_profit_pct", "exit_mode", "stop_reentry_mode", "trailing_activation_pct", "trailing_distance_pct", "trailing_reentry_mode"},
                {"max_entries_per_day", "risk_regime", "risk_per_trade_pct", "max_exposure_pct", "leverage"},
            )]
            if sum(bool(group) for group in groups) != 1 or set(changes) != set.union(*groups):
                raise ValueError("AI 候選每次只可修改一類：進場、出場或倉位風險")
            for field, value in changes.items():
                if field == "intraday_entry":
                    if value not in {"breakout", "pullback"}:
                        raise ValueError("invalid intraday entry")
                elif field in {"max_holding_bars", "max_entries_per_day"}:
                    if value is not None and (type(value) is not int or value < 1):
                        raise ValueError("limits require positive integers or null")
                elif field in {"higher_timeframe_filter", "intraday_strong_close"}:
                    if type(value) is not bool:
                        raise ValueError("higher_timeframe_filter must be boolean")
                elif field == "risk_regime":
                    if value not in {"fixed", "slow_slope", "loss_streak"}:
                        raise ValueError("invalid risk regime")
                elif field == "trailing_reentry_mode":
                    if value not in {"inherit", "exit_high_breakout", "pullback_reclaim"}:
                        raise ValueError("trailing_reentry_mode 無效")
                elif field == "stop_reentry_mode":
                    if value not in {"immediate", "signal_reset"}:
                        raise ValueError("stop_reentry_mode 無效")
                elif field == "exit_mode":
                    if value not in {"fixed", "signal"}:
                        raise ValueError("exit_mode 無效")
                elif isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                    raise ValueError("候選數值必須為有限數字")
                elif field in {"fast", "slow", "lookback"} and type(value) is not int:
                    raise ValueError("週期必須為整數")
            if not args.note.strip():
                raise ValueError("AI 自訂變更必須提供 --note，說明參考證據與假設")
            advice = replace(advice, decision="agent_proposed", changes=changes,
                             headline="AI 根據此版本回測提出受控候選", explanation=args.note)
        if not advice.has_candidate:
            request_repository.skip(
                request.request_id, decision=advice.decision,
                summary=advice.explanation, validation_plan=advice.validation_plan,
            )
            payload = _analysis_payload(repository, run, selected.result, advice)
            payload.update(request_id=request.request_id, request_status="skipped", evidence=evidence_summary)
            _print_json(payload)
            return
        comparisons = []
        selected_candidate = None
        for item in evidence:
            config, fast, slow = _candidate_settings(item.run, item.config, advice)
            if config.leverage != 1:
                raise ValueError("目前策略優化固定 1 倍槓桿")
            strategy = strategy_for_run(item.run, config, fast, slow, **{
                field: value for field, value in advice.changes.items()
                if field in {"lookback", "momentum_threshold", "entry_deviation"}
            })
            result = BacktestEngine(config).run(
                item.signal_candles, strategy, evaluation_start_ms=item.run.since_ms,
            )
            if config == item.config and result.strategy_name == item.result.strategy_name:
                raise ValueError("候選設定與父版本相同，不能建立虛假的下一版")
            note = (args.note.strip() or request.objective or advice.headline)[:120]
            candidate = repository.save(
                result=result, candles=item.candles, config=config, stage="development",
                note=f"AI 優化 #{request.request_id}：{note}；來源 {item.run.stage} 已供優化參考。"[:200],
                fast_period=fast if item.run.fast_period is not None else None,
                slow_period=slow if item.run.slow_period is not None else None,
                base_run_key=run.run_key, signal_candles=item.signal_candles,
            )
            comparisons.append(_finite(dict(
                source_run_key=item.run.run_key, candidate_run_key=candidate.run_key,
                source_stage=item.run.stage, source_used_for_tuning=True,
                since_ms=item.run.since_ms, until_ms=item.run.until_ms,
                base_metrics=asdict(item.result.metrics), candidate_metrics=asdict(result.metrics),
            )))
            if item.run.run_key == run.run_key:
                selected_candidate = candidate
        request_repository.complete(
            request.request_id, candidate_run_key=selected_candidate.run_key,
            decision=advice.decision, changes=advice.changes,
            summary=advice.explanation, validation_plan=advice.validation_plan,
            comparisons=comparisons,
        )
        _print_json(dict(
            status="candidate_saved", request_id=request.request_id, request_status="completed",
            base=_run_summary(repository, run), candidate=_run_summary(repository, selected_candidate),
            changes=advice.changes, evidence=evidence_summary, comparisons=comparisons,
            validation_plan=advice.validation_plan, promotion="not_validated",
        ))
    except (ValueError, RuntimeError) as exc:
        if request is not None:
            request_repository.fail(request.request_id, str(exc))
        parser.error(str(exc))


def _list_versions(
    repository: BacktestRunRepository, limit: int
) -> dict[str, Any]:
    versions = repository.list_strategy_versions(limit)
    return {
        "versions": [
            {
                "version": version.version_number,
                "strategy_key": version.strategy_key,
                "based_on_strategy_key": version.previous_strategy_key,
                "symbol": version.symbol,
                "timeframe": version.timeframe,
                "strategy": version.strategy_family,
                "fast_period": version.fast_period,
                "slow_period": version.slow_period,
                "stop_loss_pct": version.stop_loss_pct,
                "take_profit_pct": version.take_profit_pct,
                "leverage": version.leverage,
                "policy": json.loads(version.policy_json),
                "hypothesis": version.hypothesis,
                "experiments": [
                    _run_summary(repository, run)
                    for run in repository.list_runs_for_strategy(
                        version.strategy_key
                    )
                ],
            }
            for version in versions
        ]
    }


def _queue_payload(
    requests: OptimizationRequestRepository,
    runs: BacktestRunRepository,
) -> dict[str, Any]:
    pending = requests.list_requests("pending")
    return {
        "pending": [
            {
                "request_id": item.request_id,
                "strategy_key": item.strategy_key,
                "evidence_run_keys": item.evidence_run_keys,
                "objective": item.objective,
                "base": (
                    _run_summary(runs, run)
                    if (run := runs.get_run(item.base_run_key)) is not None
                    else {"run_key": item.base_run_key, "missing": True}
                ),
            }
            for item in pending
        ]
    }


def _reproduce(
    db_path: Path, exchange: str, run: BacktestRun
) -> tuple[list[Candle], list[Candle], BacktestResult, BacktestConfig]:
    return reproduce_run(db_path, exchange, run)


def _candidate_settings(
    run: BacktestRun,
    config: BacktestConfig,
    advice: ResearchAdvice,
) -> tuple[BacktestConfig, int | None, int | None]:
    values = asdict(config)
    fast, slow = run.fast_period, run.slow_period
    for field, value in advice.changes.items():
        if field == "fast":
            fast = int(value)
        elif field == "slow":
            slow = int(value)
        elif field in {"stop_loss_pct", "take_profit_pct"}:
            values[field] = float(value) / 100
        elif field in {"trailing_activation_pct", "trailing_distance_pct"}:
            values[field.removesuffix("_pct")] = float(value) / 100 if value else None
        elif field == "trend_entry_buffer_pct":
            values["trend_entry_buffer"] = float(value) / 100
        elif field == "intraday_min_atr_pct":
            values["intraday_min_atr_fraction"] = float(value) / 100
        elif field == "risk_per_trade_pct":
            values["risk_per_trade"] = float(value) / 100
        elif field == "max_exposure_pct":
            values["max_exposure_fraction"] = float(value) / 100
        elif field in {"lookback", "momentum_threshold", "entry_deviation"}:
            continue
        elif field in values:
            values[field] = value
        else:
            raise ValueError(f"unsupported advisor change: {field}")
    return BacktestConfig(**values), fast, slow


def _analysis_payload(
    repository: BacktestRunRepository,
    run: BacktestRun,
    result: BacktestResult,
    advice: ResearchAdvice,
) -> dict[str, Any]:
    return {
        "status": "candidate_available" if advice.has_candidate else "no_change",
        "base": _run_summary(repository, run),
        "metrics": _finite(asdict(result.metrics)),
        "advice": asdict(advice),
    }


def _run_summary(
    repository: BacktestRunRepository, run: BacktestRun
) -> dict[str, Any]:
    version = repository.get_strategy_version_for_run(run.run_key)
    return {
        "version": version.version_number if version else None,
        "strategy_key": version.strategy_key if version else None,
        "run_key": run.run_key,
        "symbol": run.symbol,
        "timeframe": run.timeframe,
        "strategy": run.strategy_name,
        "policy": json.loads(run.policy_json),
        "research_plan_id": run.research_plan_id,
        "stage": run.stage,
        "since_ms": run.since_ms,
        "until_exclusive_ms": run.until_ms + TIMEFRAMES_MS[run.timeframe],
        "initial_cash": run.initial_cash,
        "fee_bps": run.fee_bps,
        "slippage_bps": run.slippage_bps,
        "data_fingerprint": run.data_fingerprint,
        "total_return": run.total_return,
        "maximum_drawdown": run.maximum_drawdown,
        "trades": run.number_of_trades,
    }


def _finite(value: Any) -> Any:
    if isinstance(value, float) and not isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _finite(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_finite(item) for item in value]
    return value


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(_finite(payload), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
