"""Development trial 6 (Objective B): cross-sectional momentum, walk-forward over L (choose 2022-23, check 2024-25)."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from app.backtest import multi_trend
from app.backtest.cross_sectional import run_cross_sectional
from app.backtest.multi_trend import TrendConfig, run_multi_trend
from scripts.research_multi_coin_trend import COSTS, inputs

OUTPUT = Path("data/cross-sectional-momentum-research.json")
DESIGN = Path("docs/research/2026-10-30-cross-sectional-momentum-design.md")
LOOKBACKS = (7, 14, 28)
SOURCES = ("app/backtest/cross_sectional.py", "app/backtest/multi_trend.py", "scripts/research_cross_sectional_momentum.py", str(DESIGN))


def with_curve(run, *args) -> tuple[dict, list[float]]:
    """Run and also capture the daily equity curve the engine passes to its metrics."""
    captured = []
    original = multi_trend.calculate_metrics

    def capture(curve, *rest, **kw):
        captured.extend(p.equity for p in curve)
        return original(curve, *rest, **kw)
    multi_trend.calculate_metrics = capture
    try:
        return run(*args), captured
    finally:
        multi_trend.calculate_metrics = original


def weekly(curve: list[float]) -> np.ndarray:
    points = np.asarray(curve[::7])
    return points[1:] / points[:-1] - 1


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    bars, funding, universe = inputs()
    rows, curves = [], {}
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        _, curves[("ts30", year)] = with_curve(run_multi_trend, bars, funding, universe, TrendConfig(30, 5, 5), start, end)
        for case, (fee, slip) in COSTS.items():
            for lookback in LOOKBACKS:
                result, curve = with_curve(run_cross_sectional, bars, funding, universe, TrendConfig(lookback, fee, slip), start, end)
                if case == "primary":
                    curves[(lookback, year)] = curve
                rows.append(dict(year=year, cost_case=case, lookback=lookback, result=result))
                m = result["metrics"]
                print(year, case, lookback, f"return={m['total_return']:+.2%} dd={m['maximum_drawdown']:.2%}",
                      f"fees={result['fees']:.0f} slip={result['slippage']:.0f} funding={result['funding_paid']:.0f}",
                      f"stop={result['account_stop_at_ms'] is not None}", flush=True)

    def ret(year: int, case: str, lookback: int) -> float:
        return next(r["result"]["metrics"]["total_return"] for r in rows
                    if (r["year"], r["cost_case"], r["lookback"]) == (year, case, lookback))
    selection = {L: (ret(2022, "primary", L) + ret(2023, "primary", L)) / 2 for L in LOOKBACKS}
    chosen = max(LOOKBACKS, key=lambda L: (round(selection[L], 12), L))
    chosen_rows = [r for r in rows if r["lookback"] == chosen]
    mean = {c: sum(ret(y, c, chosen) for y in range(2022, 2026)) / 4 for c in COSTS}
    check = (ret(2024, "primary", chosen) + ret(2025, "primary", chosen)) / 2
    worst = min(r["result"]["metrics"]["total_return"] for r in chosen_rows)
    drawdown = min(r["result"]["metrics"]["maximum_drawdown"] for r in chosen_rows)
    xs = np.concatenate([weekly(curves[(chosen, y)]) for y in range(2022, 2026)])
    ts = np.concatenate([weekly(curves[("ts30", y)]) for y in range(2022, 2026)])
    checks = dict(selection_mean_2022_2023=selection, chosen_lookback=chosen, mean_by_cost=mean, check_2024_2025=check,
                  worst_year=worst, worst_drawdown=drawdown, weekly_correlation_with_trial4=float(np.corrcoef(xs, ts)[0, 1]),
                  passed=mean["primary"] >= .10 and check >= .10 and drawdown >= -.40 and worst >= -.40 and mean["doubled"] > 0)
    artifact = dict(schema="cross_sectional_momentum_walkforward_v1", objective="B", design=str(DESIGN), development_trial=6,
                    trials_in_this_experiment=len(LOOKBACKS), sealed_data_used=False,
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES}, rows=rows, checks=checks,
                    decision="eligible_for_forward_paper_registration" if checks["passed"] else "reject")
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(dict(checks=checks, decision=artifact["decision"]), indent=1))


if __name__ == "__main__":
    main()
