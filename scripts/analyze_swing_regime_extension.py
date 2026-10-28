"""Diagnose baseline swing trades by daily SMA regime and breakout extension.

Diagnostics only: groups the saved portfolio_swing_failure_exit trades by
information known at the entry decision. Grouped results are not fills of a
filtered strategy and do not create a candidate.
"""
from collections import defaultdict
import json
from pathlib import Path

from app.data.aggregation import completed_four_hour_bars
from app.data.models import Candle

BASELINE = Path("data/perpetual-swing-failure-exit.json")
OUTPUT = Path("data/swing-regime-extension-diagnostics.json")


def _bucket(extension: float) -> str:
    return "<1" if extension < 1 else "1-2" if extension < 2 else ">=2"


def main() -> None:
    tape = [Candle("binance-usdm", "BTC/USDT", "1h", int(r["open_time"]),
                   *[float(r[k]) for k in ("open", "high", "low", "close", "volume")])
            for r in json.loads(Path("data/btc-perpetual-1h/klines.json").read_text())]
    index = {c.timestamp_ms: i for i, c in enumerate(tape)}
    # Daily close = last completed 1h close of each UTC day.
    daily: dict[int, float] = {}
    for candle in tape:
        daily[candle.timestamp_ms // 86400000] = candle.close
    days = sorted(daily)
    rows = []
    for row in json.loads(BASELINE.read_text(encoding="utf-8"))["rows"]:
        groups: dict[str, dict] = defaultdict(lambda: dict(count=0, pnl=0.0, wins=0))
        for trade in row["result"]["trades"]:
            if trade["sleeve"] != "swing":
                continue
            side = "long" if trade["direction"] == 1 else "short"
            decision = index[trade["entry_timestamp_ms"] - 3600000]
            bars = completed_four_hour_bars(tape[max(0, decision - 400):decision + 1])
            ranges = [max(bars[k].high - bars[k].low, abs(bars[k].high - bars[k - 1].close),
                          abs(bars[k].low - bars[k - 1].close)) for k in range(len(bars) - 14, len(bars))]
            atr = sum(ranges) / 14
            reference = bars[-22:-2]
            boundary = (max(c.high for c in reference) if trade["direction"] == 1
                        else min(c.low for c in reference))
            extension = (bars[-1].close - boundary) * trade["direction"] / atr
            keys = [f"extension_atr|{side}|{_bucket(extension)}"]
            prior = [daily[d] for d in days if d < trade["entry_timestamp_ms"] // 86400000]
            for length in (50, 200):
                if len(prior) >= length:
                    regime = "above" if prior[-1] > sum(prior[-length:]) / length else "below"
                    keys.append(f"daily_sma{length}|{side}|{regime}")
            for key in keys:
                groups[key]["count"] += 1
                groups[key]["pnl"] += trade["pnl"]
                groups[key]["wins"] += trade["pnl"] > 0
        rows.append(dict(year=row["year"], cost_multiplier=row["cost_multiplier"],
                         input_fingerprints=row["input_fingerprints"],
                         groups={k: groups[k] for k in sorted(groups)}))
    OUTPUT.write_text(json.dumps(dict(
        schema="swing_regime_extension_diagnostics_v1", baseline="portfolio_swing_failure_exit",
        used_for_tuning=True, independent_validation=False,
        note="Grouped saved trades; not a filtered-strategy replay.", rows=rows),
        ensure_ascii=False, indent=2), encoding="utf-8")
    for row in rows:
        print(row["year"], row["cost_multiplier"])
        for key, value in row["groups"].items():
            print(f"  {key:28s} n={value['count']:3d} pnl={value['pnl']:8.1f} wins={value['wins']}")


if __name__ == "__main__":
    main()
