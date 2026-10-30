"""Core-satellite portfolio screen (plan: docs/research/2026-10-30-core-satellite-plan.md).

70% BTC spot 50-day filter, 20% BTC carry (0.001 BTC rounding), 10% multi-coin trend L=30, as separate
sub-accounts reset to 3,000 USDT each year. Screening evidence only (weights chosen after seeing results).
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest import funding_carry, trend_filter
from app.backtest.funding_carry import CarryConfig, run_funding_carry
from app.backtest.multi_trend import TrendConfig, run_multi_trend
from app.backtest.trend_filter import FilterConfig, run_trend_filter
from scripts.fetch_btc_spot_2022_2023 import KNOWN_OUTAGES
from scripts.fetch_btc_spot_daily import OUTPUT as FILTER_BARS
from scripts.research_btc_trend_filter import COSTS as FILTER_COSTS
from scripts.research_carry_funding_pause import assets
from scripts.research_cross_sectional_momentum import with_curve
from scripts.research_funding_carry import COSTS as CARRY_COSTS
from scripts.research_multi_coin_trend import COSTS as TREND_COSTS, inputs
from scripts.research_small_capital_lots import LotCarryBook, portfolio_carry_book

OUTPUT = Path("data/core-satellite-research.json")
PLAN = Path("docs/research/2026-10-30-core-satellite-plan.md")
CAPITAL = 3000.0
WEIGHTS = dict(core=.70, carry=.20, satellite=.10)
CASES = ("primary", "mid", "doubled", "stress")
SOURCES = ("scripts/research_core_satellite.py", str(PLAN))
DAY_MS = 86400000


def filter_curve(bars: dict, costs: tuple, start: int, end: int) -> list[float]:
    captured = {}
    original = trend_filter.calculate_metrics

    def capture(points, *rest, **kw):
        captured.update({p.timestamp_ms: p.equity for p in points})
        return original(points, *rest, **kw)
    trend_filter.calculate_metrics = capture
    try:
        run_trend_filter(bars, FilterConfig(50, *costs, initial_cash=CAPITAL * WEIGHTS["core"]), start, end)
    finally:
        trend_filter.calculate_metrics = original
    return [captured[t] for t in range(start, end, DAY_MS)]


def carry_curve(btc: tuple, costs: tuple, start: int, end: int) -> list[float]:
    tape, marks, funding, spot = btc
    hours = range(start, end, 3600000)
    funding_carry.CarryBook = LotCarryBook
    try:
        result = run_funding_carry([tape[t] for t in hours], [marks[t] for t in hours],
                                   [f for f in funding if start <= f.timestamp_ms < end], {t: spot[t] for t in hours if t in spot},
                                   CarryConfig(*costs, initial_cash=CAPITAL * WEIGHTS["carry"]), frozenset(KNOWN_OUTAGES))
    finally:
        funding_carry.CarryBook = portfolio_carry_book
    hourly = dict(result["equity_curve"])
    return [hourly[t + 23 * 3600000] for t in range(start, end, DAY_MS)]


def satellite_curve(data: tuple, costs: tuple, start: int, end: int) -> list[float]:
    bars, funding, universe = data
    _, curve = with_curve(run_multi_trend, bars, funding, universe,
                          TrendConfig(30, *costs, initial_cash=CAPITAL * WEIGHTS["satellite"]), start, end)
    return curve[1:]


def drawdown(values: list[float]) -> float:
    peak, worst = values[0], 0.0
    for v in values:
        peak = max(peak, v)
        worst = min(worst, v / peak - 1)
    return worst


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    filter_bars = {int(t): tuple(v) for t, v in json.loads(FILTER_BARS.read_text(encoding="utf-8"))}
    btc, trend = assets()["BTC"], inputs()
    costs = dict(core=list(FILTER_COSTS.values()), carry=list(CARRY_COSTS.values()), satellite=list(TREND_COSTS.values()))
    rows = []
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        closes = [filter_bars[t][3] for t in range(start, end, DAY_MS)]
        hold = [CAPITAL * c / filter_bars[start][0] for c in closes]
        for i, case in enumerate(CASES):
            parts = dict(core=filter_curve(filter_bars, costs["core"][i], start, end),
                         carry=carry_curve(btc, costs["carry"][i], start, end),
                         satellite=satellite_curve(trend, costs["satellite"][i], start, end))
            total = [CAPITAL] + [sum(p[d] for p in parts.values()) for d in range(len(closes))]
            row = dict(year=year, cost_case=case, total_return=total[-1] / CAPITAL - 1, max_drawdown=drawdown(total),
                       parts={k: dict(start=CAPITAL * WEIGHTS[k], end=v[-1], return_=v[-1] / (CAPITAL * WEIGHTS[k]) - 1,
                                      max_drawdown=drawdown([CAPITAL * WEIGHTS[k]] + v)) for k, v in parts.items()},
                       btc_hold=dict(return_=hold[-1] / CAPITAL - 1, max_drawdown=drawdown([CAPITAL] + hold)))
            rows.append(row)
            print(year, case, f"total {row['total_return']:+.1%} dd {row['max_drawdown']:.1%} |",
                  " ".join(f"{k} {v['return_']:+.1%}" for k, v in row["parts"].items()),
                  f"| hold {row['btc_hold']['return_']:+.1%} dd {row['btc_hold']['max_drawdown']:.1%}", flush=True)
    mean = {c: sum(r["total_return"] for r in rows if r["cost_case"] == c) / 4 for c in CASES}
    multiple = {c: 1.0 for c in CASES}
    for r in rows:
        multiple[r["cost_case"]] *= 1 + r["total_return"]
    checks = dict(mean_by_cost=mean, compounded_4y_multiple=multiple,
                  worst_year=min(r["total_return"] for r in rows), worst_drawdown=min(r["max_drawdown"] for r in rows))
    checks["passed"] = (mean["primary"] >= .10 and checks["worst_drawdown"] >= -.40 and checks["worst_year"] >= -.40
                        and mean["doubled"] > 0)
    artifact = dict(schema="core_satellite_screen_v1", plan=str(PLAN), weights=WEIGHTS, capital=CAPITAL,
                    screening_only=True, satellite_lot_minimums_modelled=False, sealed_data_used=False,
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES}, rows=rows, checks=checks)
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(checks, indent=1))


if __name__ == "__main__":
    main()
