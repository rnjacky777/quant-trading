"""Execution feasibility at 200 USDT: reuses the 3,000 USDT lot-rounding wrappers (same rules, different capital)."""
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from scripts.research_carry_funding_pause import assets
from scripts.research_funding_carry import COSTS as CARRY_COSTS
from scripts.research_risk_budget import COSTS as TREND_COSTS, late_inputs
from scripts.research_small_capital_lots import carry_run, trend_run
from scripts.validate_baseline_2022_2023 import load_inputs

OUTPUT = Path("data/small-capital-200-research.json")
CAPITAL = 200
SOURCES = ("scripts/research_small_capital_200.py", "scripts/research_small_capital_lots.py",
           "docs/research/2026-10-29-small-capital-lot-design.md")


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    budget = json.loads(Path("data/perpetual-risk-budget-055.json").read_text(encoding="utf-8"))
    limits = PortfolioLimits(**budget["portfolio_limits"])
    template = next(r for r in budget["rows"] if r["variant"] == "portfolio_swing_failure_exit")
    early, late = load_inputs(), late_inputs()
    rows = []
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        tape, marks, funding = early[:3] if year < 2024 else late
        period = [c for c in tape if start - 243 * 3600000 <= c.timestamp_ms < end]
        for fee, slip in TREND_COSTS:
            for rounding in (False, True):
                strategies = dict(intraday=DirectionalSweepStructureConfirmStrategy(), swing=DirectionalSwingEfficiencyStrategy())
                sleeves = [ResearchSleeve(s["name"], strategies[s["name"]], replace(
                    PerpetualResearchConfig(**s["config"]), initial_cash=CAPITAL, fee_bps=fee, slippage_bps=slip))
                    for s in template["sleeves"]]
                engine = PortfolioResearchEngine(sleeves, limits, directional_loss_guard=True, swing_failure_exit=True)
                result, rejected = trend_run(engine, rounding, candles=period, evaluation_start_ms=start,
                                             marks=[m for m in marks if start <= m.timestamp_ms < end],
                                             funding=[f for f in funding if start <= f.timestamp_ms < end])
                rows.append(dict(book="trend", year=year, cost_case=f"{fee}/{slip}", capital=CAPITAL, rounding=rounding,
                                 metrics=result["metrics"], entries=len(result["trades"]), rejected_below_minimum=rejected))
                print("trend", year, f"{fee}/{slip}", rounding, f"{result['metrics']['total_return']:+.3%}",
                      len(result["trades"]), rejected, flush=True)
    btc = assets()["BTC"]
    for year in range(2022, 2026):
        for case, costs in CARRY_COSTS.items():
            for rounding in (False, True):
                result, skipped = carry_run(btc, year, costs, CAPITAL, rounding)
                rows.append(dict(book="carry", year=year, cost_case=case, capital=CAPITAL, rounding=rounding,
                                 metrics=result["metrics"], rebalances=len(result["rebalances"]), skipped_rebalances=skipped,
                                 liquidated_at_ms=result["liquidated_at_ms"]))
                print("carry", year, case, rounding, f"{result['metrics']['total_return']:+.3%}", skipped, flush=True)
    artifact = dict(schema="small_capital_200_v1", capital=CAPITAL, sealed_data_used=False,
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES}, rows=rows)
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
