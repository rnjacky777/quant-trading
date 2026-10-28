"""Reproduce saved evidence and compare two fixed versions over registered periods."""
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import json
from math import isclose, isfinite
from pathlib import Path

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestResult
from app.backtest.periods import annual_performance
from app.backtest.reproduction import config_for_run, reproduce_run, strategy_for_run
from app.backtest.research import ResearchPlanRepository
from app.backtest.runs import BacktestRun, BacktestRunRepository
from app.config.settings import Settings
from app.data.models import TIMEFRAMES_MS
from app.data.repository import CandleRepository


def summary(run: BacktestRun, result: BacktestResult) -> dict[str, object]:
    return dict(
        run_key=run.run_key, strategy_key=run.strategy_key, stage=run.stage,
        since=datetime.fromtimestamp(run.since_ms/1000, timezone.utc).isoformat(),
        until_exclusive=datetime.fromtimestamp((run.until_ms+TIMEFRAMES_MS[run.timeframe])/1000, timezone.utc).isoformat(),
        metrics=asdict(result.metrics), final_equity=result.final_equity,
        annual=annual_performance(result), exit_reasons=dict(Counter(trade.exit_reason for trade in result.trades)),
        planned_risk_breaches=sum(trade.pnl < -trade.planned_risk - 1e-7 for trade in result.trades if trade.planned_risk > 0),
        policy=json.loads(run.policy_json),
    )


def finite(value):
    if isinstance(value, float) and not isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: finite(item) for key, item in value.items()}
    if isinstance(value, list):
        return [finite(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-run-key", required=True)
    parser.add_argument("--candidate-run-key", required=True)
    parser.add_argument("--research-plan-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    settings = Settings.from_env()
    repo = BacktestRunRepository(settings.db_path)
    base, candidate = repo.get_run(args.base_run_key), repo.get_run(args.candidate_run_key)
    if base is None or candidate is None:
        parser.error("selected experiment does not exist")
    if (base.symbol, base.timeframe, base.strategy_name) != (candidate.symbol, candidate.timeframe, candidate.strategy_name):
        parser.error("comparison requires identical entry strategy and market")
    plans = ResearchPlanRepository(settings.db_path).list_plans()
    plan = next((item for item in plans if item.plan_id == args.research_plan_id), None)
    if plan is None:
        parser.error("research plan does not exist")
    evidence = []
    for run in reversed(repo.list_recent(100)):
        result = reproduce_run(settings.db_path, settings.exchange_id, run)[2]
        if not isclose(result.final_equity, run.final_equity, rel_tol=1e-10):
            raise ValueError(f"saved result did not reproduce: {run.run_key}")
        evidence.append(summary(run, result))
    comparisons = []
    data = CandleRepository(settings.db_path)
    for stage in ("development", "validation"):
        since, until = getattr(plan, f"{stage}_since"), getattr(plan, f"{stage}_until")
        ResearchPlanRepository(settings.db_path).validate(plan.plan_id, stage, since, until)
        for label, source in (("V1", base), ("V2", candidate)):
            interval = TIMEFRAMES_MS[source.timeframe]
            warmup = source.slow_period or 1
            candles = data.list_range(settings.exchange_id, source.symbol, source.timeframe, since, until)
            if not candles or candles[0].timestamp_ms != since or candles[-1].timestamp_ms + interval != until:
                raise ValueError("registered period does not have full candle boundaries")
            before = data.list_range(settings.exchange_id, source.symbol, source.timeframe, max(0, since-warmup*interval), since) if since else []
            config = config_for_run(source)
            result = BacktestEngine(config).run(before+candles,
                                               strategy_for_run(source, config), evaluation_start_ms=since)
            run = repo.save(result, candles, config, stage,
                            f"預先登記區間的 {label} 固定參數比較；歷史已查看，不作獨立未見驗證。",
                            source.fast_period, source.slow_period, base_run_key=source.run_key,
                            signal_candles=before+candles, research_plan_id=plan.plan_id)
            comparisons.append(dict(version=label, **summary(run, result)))
    report = dict(plan=asdict(plan), saved_evidence=evidence, fixed_period_comparisons=comparisons,
                  promotion="not_validated", holdout_evaluated=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(finite(report), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(finite(comparisons), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
