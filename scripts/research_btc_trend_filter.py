"""Development trial 8 (Objective B): BTC spot long-term moving-average filter, walk-forward over N."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.trend_filter import FilterConfig, run_trend_filter
from scripts.fetch_btc_spot_daily import OUTPUT as BARS

OUTPUT = Path("data/btc-trend-filter-research.json")
DESIGN = Path("docs/research/2026-10-30-btc-trend-filter-design.md")
WINDOWS = (50, 100, 200)
COSTS = {"primary": (10, 5), "10/10": (10, 10), "doubled": (20, 10), "stress": (30, 15)}
SOURCES = ("app/backtest/trend_filter.py", "scripts/research_btc_trend_filter.py", "scripts/fetch_btc_spot_daily.py", str(DESIGN))


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    bars = {int(t): tuple(v) for t, v in json.loads(BARS.read_text(encoding="utf-8"))}
    rows, benchmarks = [], {}
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        prices = [bars[t] for t in range(start, end, 86400000)]
        peak = dd = 0.0
        for b in prices:
            peak = max(peak, b[3])
            dd = min(dd, b[3] / peak - 1)
        benchmarks[year] = dict(btc_hold_return=prices[-1][3] / prices[0][0] - 1, btc_hold_max_drawdown=dd)
        for case, (fee, slip) in COSTS.items():
            for window in WINDOWS:
                result = run_trend_filter(bars, FilterConfig(window, fee, slip), start, end)
                rows.append(dict(year=year, cost_case=case, window=window, result=result))
                m = result["metrics"]
                print(year, case, window, f"return={m['total_return']:+.2%} dd={m['maximum_drawdown']:.2%}",
                      f"trades={result['trades']} invested_days={result['invested_days']}", flush=True)

    def ret(year: int, case: str, window: int) -> float:
        return next(r["result"]["metrics"]["total_return"] for r in rows if (r["year"], r["cost_case"], r["window"]) == (year, case, window))
    selection = {n: (ret(2022, "primary", n) + ret(2023, "primary", n)) / 2 for n in WINDOWS}
    chosen = max(WINDOWS, key=lambda n: (round(selection[n], 12), n))
    chosen_rows = [r for r in rows if r["window"] == chosen]
    mean = {c: sum(ret(y, c, chosen) for y in range(2022, 2026)) / 4 for c in COSTS}
    check = (ret(2024, "primary", chosen) + ret(2025, "primary", chosen)) / 2
    worst = min(r["result"]["metrics"]["total_return"] for r in chosen_rows)
    drawdown = min(r["result"]["metrics"]["maximum_drawdown"] for r in chosen_rows)
    checks = dict(selection_mean_2022_2023=selection, chosen_window=chosen, mean_by_cost=mean, check_2024_2025=check,
                  worst_year=worst, worst_drawdown=drawdown,
                  passed=mean["primary"] >= .10 and check >= .10 and drawdown >= -.40 and worst >= -.40 and mean["doubled"] > 0)
    artifact = dict(schema="btc_trend_filter_walkforward_v1", objective="B", design=str(DESIGN), development_trial=8,
                    trials_in_this_experiment=len(WINDOWS), sealed_data_used=False,
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
                    benchmarks=benchmarks, rows=rows, checks=checks,
                    decision="eligible_for_sealed_validation_request" if checks["passed"] else "reject")
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(dict(benchmarks=benchmarks, checks=checks, decision=artifact["decision"]), indent=1))


if __name__ == "__main__":
    main()
