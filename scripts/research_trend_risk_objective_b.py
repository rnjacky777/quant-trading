"""Development trial 5 (Objective B): one preregistered higher-risk setting of the trend baseline."""
from dataclasses import asdict, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from scripts.research_risk_budget import COSTS, diagnostics, late_inputs
from scripts.validate_baseline_2022_2023 import load_inputs

OUTPUT = Path("data/trend-risk-objective-b.json")
DESIGN = Path("docs/research/2026-10-30-trend-risk-objective-b-design.md")
PARENT = Path("data/perpetual-risk-budget-055.json")
SOURCES = ("scripts/research_trend_risk_objective_b.py", str(DESIGN))
CANDIDATE = dict(risk_per_trade=.01, max_exposure=1.0)
CANDIDATE_LIMITS = dict(max_open_stop_risk=.04, max_gross_exposure=1.0)


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    saved = json.loads(PARENT.read_text(encoding="utf-8"))
    parents = {(r["year"], r["fee_bps"], r["slippage_bps"]): r for r in saved["rows"] if r["variant"] == "portfolio_swing_failure_exit"}
    early, late = load_inputs(), late_inputs()
    rows = []
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        tape, marks, funding = early[:3] if year < 2024 else late
        period = [c for c in tape if start - 243 * 3600000 <= c.timestamp_ms < end]
        inputs = dict(evaluation_start_ms=start, marks=[m for m in marks if start <= m.timestamp_ms < end],
                      funding=[f for f in funding if start <= f.timestamp_ms < end])
        for fee, slip in COSTS:
            parent = parents[(year, fee, slip)]
            for variant, sleeve_changes, limit_changes in (("parent", {}, {}), ("candidate", CANDIDATE, CANDIDATE_LIMITS)):
                strategies = dict(intraday=DirectionalSweepStructureConfirmStrategy(), swing=DirectionalSwingEfficiencyStrategy())
                sleeves = [ResearchSleeve(s["name"], strategies[s["name"]], replace(PerpetualResearchConfig(**s["config"]), **sleeve_changes))
                           for s in parent["sleeves"]]
                limits = PortfolioLimits(**{**saved["portfolio_limits"], **limit_changes})
                result = json.loads(serialize_result(PortfolioResearchEngine(
                    sleeves, limits, directional_loss_guard=True, swing_failure_exit=True).run(period, **inputs)))
                if variant == "parent" and result["metrics"] != parent["result"]["metrics"]:
                    raise ValueError(f"{year} {fee}/{slip}: parent reproduction failed")
                rows.append(dict(year=year, fee_bps=fee, slippage_bps=slip, variant=variant, metrics=result["metrics"],
                                 diagnostics=diagnostics(result, year), limits=asdict(limits),
                                 sleeves=[dict(name=s.name, config=asdict(s.config)) for s in sleeves]))
                m = result["metrics"]
                print(variant, year, f"{fee}/{slip}", f"return={m['total_return']:+.2%} dd={m['maximum_drawdown']:.2%}",
                      f"trades={m['number_of_trades']}", flush=True)
    cand = [r for r in rows if r["variant"] == "candidate"]
    mean = {f"{f}/{s}": sum(r["metrics"]["total_return"] for r in cand if (r["fee_bps"], r["slippage_bps"]) == (f, s)) / 4
            for f, s in COSTS}
    worst = min(r["metrics"]["total_return"] for r in cand)
    drawdown = min(r["metrics"]["maximum_drawdown"] for r in cand)
    checks = dict(mean_by_cost=mean, worst_year=worst, worst_drawdown=drawdown,
                  passed=mean["5/5"] >= .10 and drawdown >= -.40 and worst >= -.40 and mean["10/10"] > 0)
    artifact = dict(schema="trend_risk_objective_b_v1", objective="B", design=str(DESIGN), development_trial=5,
                    used_for_tuning=True, sealed_data_used=False, candidate=CANDIDATE, candidate_limits=CANDIDATE_LIMITS,
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES}, rows=rows, checks=checks,
                    decision="eligible_for_sealed_validation_request" if checks["passed"] else "reject")
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(dict(checks=checks, decision=artifact["decision"]), indent=1))


if __name__ == "__main__":
    main()
