from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
from typing import Any

from app.backtest.advisor import ResearchAdvice, analyze_backtest
from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig, BacktestResult
from app.backtest.optimization import OptimizationRequestRepository
from app.backtest.runs import BacktestRun, BacktestRunRepository
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from app.strategies.trend_following import MovingAverageTrendStrategy


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
    for name in ("analyze", "optimize"):
        command = commands.add_parser(name)
        command.add_argument("--run-key", required=True)
        if name == "optimize":
            command.add_argument("--note", default="")
    request_parser = commands.add_parser(
        "optimize-request", help="Optimize one marked Dashboard request"
    )
    request_parser.add_argument("--request-id", type=int, required=True)
    request_parser.add_argument("--note", default="")
    args = parser.parse_args()

    repository = BacktestRunRepository(args.db)
    if args.command == "list":
        _print_json(_list_versions(repository, args.limit))
        return

    request_repository = OptimizationRequestRepository(args.db)
    if args.command == "queue":
        _print_json(_queue_payload(request_repository, repository))
        return

    request = None
    if args.command == "optimize-request":
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
    candles, base_result, base_config = _reproduce(args.db, args.exchange, run)
    advice = analyze_backtest(base_result, base_config)
    if args.command == "analyze":
        _print_json(_analysis_payload(repository, run, base_result, advice))
        return

    if run.stage != "development":
        if request is not None:
            request_repository.fail(request.request_id, "base version is not Development")
        parser.error("only Development results may be optimized")
    if not advice.has_candidate:
        if request is not None:
            request_repository.skip(
                request.request_id,
                decision=advice.decision,
                summary=advice.headline,
                validation_plan=advice.validation_plan,
            )
        payload = _analysis_payload(repository, run, base_result, advice)
        if request is not None:
            payload["request_id"] = request.request_id
            payload["request_status"] = "skipped"
        _print_json(payload)
        return

    candidate_config, fast, slow = _candidate_settings(run, base_config, advice)
    strategy = _strategy(run, fast, slow)
    candidate_result = BacktestEngine(candidate_config).run(candles, strategy)
    requested_objective = request.objective if request is not None else ""
    note = (
        args.note.strip()
        or requested_objective
        or f"Optimizer: {advice.headline}"
    )[:200]
    candidate = repository.save(
        result=candidate_result,
        candles=candles,
        config=candidate_config,
        stage="development",
        note=note,
        fast_period=fast if run.fast_period is not None else None,
        slow_period=slow if run.slow_period is not None else None,
        base_run_key=run.run_key,
    )
    if request is not None:
        request_repository.complete(
            request.request_id,
            candidate_run_key=candidate.run_key,
            decision=advice.decision,
            changes=advice.changes,
            summary=advice.headline,
            validation_plan=advice.validation_plan,
        )
    payload = {
        "status": "candidate_saved",
        "base": _run_summary(repository, run),
        "candidate": _run_summary(repository, candidate),
        "changes": advice.changes,
        "hypothesis": note,
        "validation_plan": advice.validation_plan,
        "comparison": {
            "total_return_delta": (
                candidate_result.metrics.total_return
                - base_result.metrics.total_return
            ),
            "maximum_drawdown_delta": (
                candidate_result.metrics.maximum_drawdown
                - base_result.metrics.maximum_drawdown
            ),
            "sharpe_delta": (
                candidate_result.metrics.sharpe_ratio
                - base_result.metrics.sharpe_ratio
            ),
        },
        "promotion": "not_validated",
    }
    if request is not None:
        payload["request_id"] = request.request_id
        payload["request_status"] = "completed"
    _print_json(payload)


def _list_versions(
    repository: BacktestRunRepository, limit: int
) -> dict[str, Any]:
    logs = repository.list_adjustments(limit)
    return {
        "versions": [
            {
                "version": log.version_number,
                "run_key": log.run_key,
                "based_on_run_key": log.previous_run_key,
                "symbol": log.symbol,
                "timeframe": log.timeframe,
                "strategy": log.strategy_family,
                "stage": log.stage,
                "total_return": log.total_return,
                "maximum_drawdown": log.maximum_drawdown,
                "trades": log.number_of_trades,
                "hypothesis": log.hypothesis,
            }
            for log in logs
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
) -> tuple[list[Candle], BacktestResult, BacktestConfig]:
    until_ms = run.until_ms + TIMEFRAMES_MS[run.timeframe]
    candles = CandleRepository(db_path).list_range(
        exchange, run.symbol, run.timeframe, run.since_ms, until_ms
    )
    if not candles:
        raise SystemExit("selected backtest candles are unavailable")
    if _fingerprint(candles) != run.data_fingerprint:
        raise SystemExit(
            "selected backtest dataset changed; exact reproduction is unavailable"
        )
    config = BacktestConfig(
        initial_cash=run.initial_cash,
        fee_bps=run.fee_bps,
        slippage_bps=run.slippage_bps,
        stop_loss_pct=run.stop_loss_pct,
        take_profit_pct=run.take_profit_pct,
        leverage=run.leverage,
    )
    strategy = _strategy(run, run.fast_period, run.slow_period)
    result = BacktestEngine(config).run(candles, strategy)
    return candles, result, config


def _strategy(
    run: BacktestRun, fast: int | None, slow: int | None
) -> MovingAverageTrendStrategy | BuyAndHoldStrategy:
    if run.fast_period is None:
        return BuyAndHoldStrategy()
    if fast is None or slow is None:
        raise ValueError("SMA strategy periods are missing")
    return MovingAverageTrendStrategy(fast, slow)


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
    log = next(
        (item for item in repository.list_adjustments(200) if item.run_key == run.run_key),
        None,
    )
    return {
        "version": log.version_number if log else None,
        "run_key": run.run_key,
        "based_on_run_key": log.previous_run_key if log else None,
        "symbol": run.symbol,
        "timeframe": run.timeframe,
        "strategy": run.strategy_name,
        "stage": run.stage,
        "total_return": run.total_return,
        "maximum_drawdown": run.maximum_drawdown,
        "trades": run.number_of_trades,
    }


def _fingerprint(candles: list[Candle]) -> str:
    digest = sha256()
    for candle in candles:
        digest.update(
            (
                f"{candle.timestamp_ms}|{candle.open:.12g}|{candle.high:.12g}|"
                f"{candle.low:.12g}|{candle.close:.12g}|{candle.volume:.12g}\n"
            ).encode()
        )
    return digest.hexdigest()


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
