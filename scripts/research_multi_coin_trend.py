"""Development trial 4 (Objective B): multi-coin time-series momentum, walk-forward over L (choose 2022-23, check 2024-25)."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.multi_trend import TrendConfig, run_multi_trend
from scripts.fetch_multi_coin_carry import ROOT as CARRY_ROOT
from scripts.fetch_multi_coin_trend import ROOT

OUTPUT = Path("data/multi-coin-trend-research.json")
DESIGN = Path("docs/research/2026-10-30-multi-coin-trend-design.md")
LOOKBACKS = (30, 60, 90)
COSTS = {"primary": (5, 5), "10/5": (10, 5), "doubled": (10, 10), "stress": (20, 10)}
SOURCES = ("app/backtest/multi_trend.py", "scripts/research_multi_coin_trend.py", "scripts/fetch_multi_coin_trend.py", str(DESIGN))


def inputs() -> tuple[dict, dict, dict]:
    universe = json.loads((CARRY_ROOT / "universe.json").read_text(encoding="utf-8"))["universe"]
    bars = {p.stem: {int(t): tuple(v) for t, v in json.loads(p.read_text(encoding="utf-8"))}
            for p in sorted((ROOT / "daily").glob("*.json"))}
    funding = {p.stem: [(int(t), r) for t, r in json.loads(p.read_text(encoding="utf-8")).get("funding", [])]
               for p in sorted((CARRY_ROOT / "hourly").glob("*.json"))}
    return bars, funding, universe


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    bars, funding, universe = inputs()
    rows, benchmarks = [], {}
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        btc = [bars["BTCUSDT"][t] for t in range(start, end, 86400000)]
        peak, dd = 0.0, 0.0
        for b in btc:
            peak = max(peak, b[3])
            dd = min(dd, b[3] / peak - 1)
        benchmarks[year] = dict(btc_hold_return=btc[-1][3] / btc[0][0] - 1, btc_hold_max_drawdown=dd)
        for case, (fee, slip) in COSTS.items():
            for lookback in LOOKBACKS:
                result = run_multi_trend(bars, funding, universe, TrendConfig(lookback, fee, slip), start, end)
                rows.append(dict(year=year, cost_case=case, lookback=lookback, result=result))
                m = result["metrics"]
                print(year, case, lookback, f"return={m['total_return']:+.2%} dd={m['maximum_drawdown']:.2%}",
                      f"intraday={result['worst_intraday_from_start']:.2%} fees={result['fees']:.0f} slip={result['slippage']:.0f}",
                      f"funding={result['funding_paid']:.0f} stop={result['account_stop_at_ms'] is not None}", flush=True)

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
    checks = dict(selection_mean_2022_2023=selection, chosen_lookback=chosen, mean_by_cost=mean, check_2024_2025=check,
                  worst_year=worst, worst_drawdown=drawdown,
                  account_stops=sum(r["result"]["account_stop_at_ms"] is not None for r in chosen_rows),
                  passed=mean["primary"] >= .10 and check >= .10 and drawdown >= -.40 and worst >= -.40 and mean["doubled"] > 0)
    artifact = dict(schema="multi_coin_trend_walkforward_v1", objective="B", design=str(DESIGN), development_trial=4,
                    trials_in_this_experiment=len(LOOKBACKS), sealed_data_used=False,
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
                    benchmarks=benchmarks, rows=rows, checks=checks,
                    decision="eligible_for_forward_paper_registration" if checks["passed"] else "reject")
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(dict(benchmarks=benchmarks, checks=checks, decision=artifact["decision"]), indent=1))


if __name__ == "__main__":
    main()
