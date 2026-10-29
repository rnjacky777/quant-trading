"""Where does the current baseline still have pre-cost edge? Diagnostics only.

Replays portfolio_swing_failure_exit with a signal observer (snapshot must match),
then groups every qualified signal, filled or not, by conditions known at the
decision bar. Outcome = fixed-horizon direction-signed move from the next 1h
open (24h intraday, 72h swing), before costs; also net of a 30 bps round trip.
Bucket thresholds come from 2024 signals only and are reused for 2025.
Overlapping events are not independent; this is not an executable return.
"""
from collections import defaultdict
from dataclasses import asdict
import json
from math import log
from pathlib import Path
import statistics as st

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.data.aggregation import completed_four_hour_bars
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy, path_efficiency
from scripts.research_perpetual_directions import fingerprint

HOUR = 3600000
HORIZON = {"intraday": 24, "swing": 72}
ROUND_TRIP = 30 / 1e4
BASELINE = Path("data/perpetual-swing-failure-exit.json")
OUTPUT = Path("data/conditional-edge-diagnostics.json")


def features(tape: list[Candle], j: int, funding: list[tuple[int, float]]) -> dict:
    """Only bars before index j (the execution bar) are used."""
    history = tape[max(0, j - 800):j]
    closes = [c.close for c in history]
    returns = [log(b / a) for a, b in zip(closes[-25:-1], closes[-24:])]
    bars = completed_four_hour_bars(history)
    fast = sum(c.close for c in bars[-20:]) / 20
    slow = sum(c.close for c in bars[-60:]) / 60
    daily = [c.close for c in history if c.timestamp_ms % 86400000 == 23 * HOUR][-20:]
    last_rate = next(r for t, r in reversed(funding) if t <= tape[j].timestamp_ms)
    return dict(realized_vol_24h=st.pstdev(returns),
                er20_4h=path_efficiency([c.close for c in bars[-21:]]),
                sma_spread_4h=fast / slow - 1,
                daily_sma20_distance=closes[-1] / (sum(daily) / len(daily)) - 1,
                return_7d=closes[-1] / closes[-169] - 1,
                funding_rate=last_rate,
                utc_session=["asia", "europe", "us"][tape[j].timestamp_ms // HOUR % 24 // 8])


def replay(tape, marks, funding, row) -> list[dict]:
    year = row["year"]
    start = 1704067200000 if year == 2024 else 1735689600000
    end = 1735689600000 if year == 2024 else 1767225600000
    period = [c for c in tape if start - 243 * HOUR <= c.timestamp_ms < end]
    period_marks = [m for m in marks if start <= m.timestamp_ms < end]
    rates = [f for f in funding if start <= f.timestamp_ms < end]
    prints = dict(candles=fingerprint([asdict(c) for c in period]), marks=fingerprint([asdict(m) for m in period_marks]),
                  funding=fingerprint([asdict(f) for f in rates]))
    if prints != row["input_fingerprints"]:
        raise ValueError("baseline inputs changed")
    strategies = dict(intraday=DirectionalSweepStructureConfirmStrategy(), swing=DirectionalSwingEfficiencyStrategy())
    sleeves = [ResearchSleeve(s["name"], strategies[s["name"]], PerpetualResearchConfig(**s["config"])) for s in row["sleeves"]]
    events: list[dict] = []
    result = PortfolioResearchEngine(sleeves, PortfolioLimits(**row["portfolio_limits"]), directional_loss_guard=True,
                                     swing_failure_exit=True).run(period, evaluation_start_ms=start, marks=period_marks,
                                                                  funding=rates, signal_observer=events.append)
    if json.loads(serialize_result(result)) != row["result"]:
        raise ValueError("instrumented replay differs from saved baseline snapshot")
    return events


def bucket(name: str, value, cuts: dict) -> str:
    if name == "utc_session":
        return value
    if name == "funding_rate":
        return "negative" if value < 0 else "at_or_below_base" if value <= 1e-4 else "above_base"
    low, high = cuts[name]
    return "low" if value < low else "mid" if value < high else "high"


def main() -> None:
    root = Path("data/btc-perpetual-1h")
    tape = [Candle("binance-usdm", "BTC/USDT", "1h", int(r["open_time"]), *[float(r[k]) for k in ("open", "high", "low", "close", "volume")])
            for r in json.loads((root / "klines.json").read_text())]
    marks = [MarkPriceCandle("binance-usdm", "BTC/USDT", int(r["open_time"]), *[float(r[k]) for k in ("open", "high", "low", "close")], timeframe="1h")
             for r in json.loads((root / "markPriceKlines.json").read_text())]
    funding = [FundingRate("binance-usdm", "BTC/USDT", int(r["fundingTime"]), float(r["fundingRate"]), float(r["markPrice"]))
               for r in json.loads((root / "funding-api.json").read_text())]
    settled = [(f.timestamp_ms, f.rate) for f in funding]
    index = {c.timestamp_ms: i for i, c in enumerate(tape)}
    signals = []
    for row in json.loads(BASELINE.read_text(encoding="utf-8"))["rows"]:
        if row["cost_multiplier"] != 1:
            continue  # raw signal set does not depend on costs
        for event in replay(tape, marks, funding, row):
            j = index[event["timestamp_ms"]]
            exit_index = j + HORIZON[event["sleeve"]]
            end = 1735689600000 if row["year"] == 2024 else 1767225600000
            if exit_index >= len(tape) or tape[exit_index].timestamp_ms >= end:
                continue  # censored at year end
            move = event["direction"] * (tape[exit_index].open / tape[j].open - 1)
            signals.append(dict(year=row["year"], sleeve=event["sleeve"], direction=event["direction"],
                                status=event["outcome"]["status"], timestamp_ms=event["timestamp_ms"],
                                gross=move, features=features(tape, j, settled)))
    numeric = ("realized_vol_24h", "er20_4h", "sma_spread_4h", "daily_sma20_distance", "return_7d")
    cuts = {}
    for name in numeric:
        values = sorted(s["features"][name] * (1 if name in ("realized_vol_24h", "er20_4h") else s["direction"])
                        for s in signals if s["year"] == 2024)
        cuts[name] = (values[len(values) // 3], values[2 * len(values) // 3])
    groups: dict[tuple, dict[int, list[float]]] = defaultdict(lambda: {2024: [], 2025: []})
    for s in signals:
        side = "long" if s["direction"] == 1 else "short"
        for name, value in s["features"].items():
            # Trend features are direction-signed: high = aligned with the trade.
            signed = value * s["direction"] if name in ("sma_spread_4h", "daily_sma20_distance", "return_7d") else value
            key = bucket(name, signed, cuts)
            for scope in ((s["sleeve"], side), (s["sleeve"], "both")):
                groups[(*scope, name, key)][s["year"]].append(s["gross"])
        groups[(s["sleeve"], side, "all", "all")][s["year"]].append(s["gross"])
    table = []
    for key, years in sorted(groups.items()):
        if min(len(years[2024]), len(years[2025])) < 10:
            continue
        stats = {y: dict(n=len(v), gross_bp=st.mean(v) * 1e4, net_bp=(st.mean(v) - ROUND_TRIP) * 1e4,
                         hit=sum(x > 0 for x in v) / len(v)) for y, v in years.items()}
        table.append(dict(sleeve=key[0], side=key[1], feature=key[2], bucket=key[3], **{str(y): s for y, s in stats.items()},
                          positive_gross_both=all(s["gross_bp"] > 0 for s in stats.values()),
                          positive_net_both=all(s["net_bp"] > 0 for s in stats.values())))
    OUTPUT.write_text(json.dumps(dict(schema="conditional_edge_diagnostics_v1", baseline="portfolio_swing_failure_exit",
        used_for_tuning=True, independent_validation=False, is_executable_portfolio_return=False,
        bucket_thresholds_from="2024 signals only", horizons_hours=HORIZON, round_trip_cost_bp=ROUND_TRIP * 1e4,
        cuts=cuts, groups=table, signal_count=len(signals)), indent=2), encoding="utf-8")
    print("signals", len(signals), {y: sum(s["year"] == y for s in signals) for y in (2024, 2025)})
    for g in table:
        if g["feature"] == "all" or g["positive_gross_both"]:
            a, b = g["2024"], g["2025"]
            print(f"{g['sleeve']:8s} {g['side']:5s} {g['feature']:20s} {g['bucket']:16s} "
                  f"24:n={a['n']:3d} g={a['gross_bp']:7.1f} | 25:n={b['n']:3d} g={b['gross_bp']:7.1f} net={b['net_bp']:7.1f}"
                  + ("  NET+BOTH" if g["positive_net_both"] else ""))


if __name__ == "__main__":
    main()
