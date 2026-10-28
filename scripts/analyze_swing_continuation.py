"""Separate entry-known close location from retrospective path diagnostics."""
from bisect import bisect_left
from collections import defaultdict
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from app.data.aggregation import completed_four_hour_bars
from app.data.models import Candle


def main() -> None:
    source = Path("data/perpetual-pa-smc.json")
    tape_path = Path("data/btc-perpetual-1h/klines.json")
    tape = [Candle("binance-usdm", "BTC/USDT", "1h", int(r["open_time"]),
                  *[float(r[k]) for k in ("open", "high", "low", "close", "volume")])
            for r in json.loads(tape_path.read_text())]
    times = [c.timestamp_ms for c in tape]
    cases = []
    for row in json.loads(source.read_text())["rows"]:
        groups = defaultdict(lambda: dict(count=0, pnl=0., wins=0, favorable_24h=0., adverse_24h=0.))
        observations = []
        followthrough = defaultdict(lambda: dict(count=0, pnl=0., wins=0))
        for trade in row["result"]["trades"]:
            if trade["sleeve"] != "swing":
                continue
            index = bisect_left(times, trade["entry_timestamp_ms"])
            assert times[index] == trade["entry_timestamp_ms"]
            bars = completed_four_hour_bars(tape[max(0, index - 244):index])
            signal_bar = bars[-1]
            side = trade["direction"]
            span = signal_bar.high - signal_bar.low
            location = ((signal_bar.close - signal_bar.low) if side == 1
                        else (signal_bar.high - signal_bar.close)) / span if span else 0.
            strong = location >= 2 / 3
            next_bar = completed_four_hour_bars(tape[index:index + 4])
            if len(next_bar) == 1:
                confirmed = side * (next_bar[0].close - signal_bar.close) > 0
                bucket = followthrough["next_4h_continues" if confirmed else "next_4h_fails"]
                bucket["count"] += 1
                bucket["pnl"] += trade["pnl"]
                bucket["wins"] += trade["pnl"] > 0
            # Future path is diagnostic only. It must never enter the signal.
            path = tape[index:index + 24]
            if len(path) != 24:
                continue
            entry = trade["entry_price"]
            favorable = max(0., max((c.high - entry) if side == 1 else (entry - c.low) for c in path)) / entry
            adverse = max(0., max((entry - c.low) if side == 1 else (c.high - entry) for c in path)) / entry
            key = "strong_close" if strong else "weak_close"
            g = groups[key]
            g["count"] += 1
            g["pnl"] += trade["pnl"]
            g["wins"] += trade["pnl"] > 0
            g["favorable_24h"] += favorable
            g["adverse_24h"] += adverse
            observations.append(dict(position_id=trade["position_id"], signal_bar=asdict(signal_bar),
                entry_known_close_location=location, pnl=trade["pnl"],
                diagnostic_only_24h_mfe=favorable, diagnostic_only_24h_mae=adverse))
        for g in groups.values():
            g["mean_24h_mfe"] = g.pop("favorable_24h") / g["count"]
            g["mean_24h_mae"] = g.pop("adverse_24h") / g["count"]
        cases.append(dict(year=row["year"], cost=row["cost_multiplier"], groups=dict(groups),
                          future_only_followthrough=dict(followthrough), observations=observations))
        print(row["year"], row["cost_multiplier"], json.dumps(dict(groups)), flush=True)
        print("Future-only followthrough:", json.dumps(dict(followthrough)), flush=True)
    Path("data/pa-smc-continuation-diagnostics.json").write_text(json.dumps(dict(
        note="Entry-known feature versus future-only diagnostic. Shared cash/quotas; no causal attribution. Years are tuning evidence.",
        sources={str(p): sha256(p.read_bytes()).hexdigest() for p in (source, tape_path)}, cases=cases), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
