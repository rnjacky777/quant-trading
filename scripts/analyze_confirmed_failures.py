"""Describe confirmed-breakout failures using only entry-known regime features."""
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.data.aggregation import completed_four_hour_bars
from app.data.models import Candle


def main() -> None:
    source = Path("data/perpetual-pa-smc-confirmation.json")
    tape_path = Path("data/btc-perpetual-1h/klines.json")
    tape = [Candle("binance-usdm", "BTC/USDT", "1h", int(r["open_time"]),
                  *[float(r[k]) for k in ("open", "high", "low", "close", "volume")])
            for r in json.loads(tape_path.read_text())]
    times = [c.timestamp_ms for c in tape]
    cases = []
    for row in json.loads(source.read_text())["rows"]:
        groups = defaultdict(lambda: dict(count=0, losses=0, pnl=0., loss_pnl=0., fees=0., slippage=0., funding=0.))
        observations = []
        for trade in row["result"]["trades"]:
            side = "long" if trade["direction"] == 1 else "short"
            labels = [f"sleeve/{trade['sleeve']}/{side}"]
            if trade["sleeve"] == "swing":
                index = bisect_left(times, trade["entry_timestamp_ms"])
                bars = completed_four_hour_bars(tape[:index])
                closes = [c.close for c in bars]
                fast, slow = sum(closes[-20:]) / 20, sum(closes[-60:]) / 60
                previous_slow = sum(closes[-61:-1]) / 60
                aligned = trade["direction"] * (slow - previous_slow) > 0
                changes = sum(abs(b - a) for a, b in zip(closes[-21:-1], closes[-20:]))
                efficiency = abs(closes[-1] - closes[-21]) / changes if changes else 0.
                regime = "directional_ER_ge_0.3" if efficiency >= .3 else "choppy_ER_lt_0.3"
                ranges = [max(bars[i].high - bars[i].low, abs(bars[i].high - bars[i-1].close),
                              abs(bars[i].low - bars[i-1].close)) for i in range(len(bars)-14, len(bars))]
                atr = sum(ranges) / 14
                separation = abs(fast - slow) / atr
                month = datetime.fromtimestamp(trade["entry_timestamp_ms"] / 1000, timezone.utc).strftime("%Y-%m")
                slope = "aligned_slow_slope" if aligned else "opposed_or_flat_slow_slope"
                clears_extreme = (bars[-1].close > bars[-2].high if trade["direction"] == 1
                                  else bars[-1].close < bars[-2].low)
                labels += [f"swing/side/{side}", f"swing/regime/{regime}/{side}",
                           f"swing/slope/{slope}/{side}", f"swing/month/{month}/{side}",
                           f"swing/exit/{trade['exit_reason']}/{side}",
                           f"swing/separation/{'ge_1_ATR' if separation >= 1 else 'lt_1_ATR'}/{side}",
                           f"swing/confirmation/{'beyond_breakout_extreme' if clears_extreme else 'inside_breakout_wick'}/{side}"]
                observations.append(dict(position_id=trade["position_id"], direction=trade["direction"],
                    entry_ms=trade["entry_timestamp_ms"], entry_known_er20=efficiency,
                    entry_known_slow_slope_aligned=aligned, entry_known_sma_separation_atr=separation,
                    entry_known_clears_breakout_extreme=clears_extreme,
                    pnl=trade["pnl"], exit_reason=trade["exit_reason"]))
            for label in labels:
                g = groups[label]
                g["count"] += 1
                g["losses"] += trade["pnl"] < 0
                g["pnl"] += trade["pnl"]
                g["loss_pnl"] += min(0., trade["pnl"])
                g["fees"] += trade["fees"]
                g["slippage"] += trade["slippage_cost"]
                g["funding"] += trade["funding"]
        cases.append(dict(year=row["year"], cost=row["cost_multiplier"], groups=dict(groups), observations=observations))
        print("CASE", row["year"], row["cost_multiplier"])
        for key, g in sorted(groups.items()):
            if "/month/" not in key and "/exit/" not in key:
                print(key, g["count"], g["losses"], round(g["pnl"], 2))
    Path("data/confirmed-failure-diagnostics.json").write_text(json.dumps(dict(
        definitions="Failure=net pnl<0, not proof of a false breakout. ER20 0.3 and SMA gap 1ATR are descriptive fixed bins, not tuned cutoffs. Regimes observed before entry. Groups overlap; do not sum groups or cost cases.",
        sources={str(p): sha256(p.read_bytes()).hexdigest() for p in (source, tape_path)}, cases=cases), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
