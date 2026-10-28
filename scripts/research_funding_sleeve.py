"""Funding-rate sleeve screen on 2024/2025 tuning data (no engine, no candidate).

Event study of forward returns after funding settlements, then one fixed rule:
when flat and a settlement prints a negative rate, buy the next 1h open, hold
72h, no stacking, at 50% notional. Costs: 10+5 bps per side (x2 for stress)
plus actual funding paid or received. Does not touch the 2022/2023 validation tape.
"""
import json
from pathlib import Path
import statistics as st

YEARS = {2024: (1704067200000, 1735689600000), 2025: (1735689600000, 1767225600000)}
HOUR = 3600000
OUTPUT = Path("data/funding-sleeve-research.json")


def _level(rate: float) -> str:
    return "negative" if rate < 0 else "below_0.01pct" if rate < 1e-4 else "0.01_to_0.03pct" if rate < 3e-4 else "above_0.03pct"


def main() -> None:
    root = Path("data/btc-perpetual-1h")
    klines = json.loads((root / "klines.json").read_text())
    opens = {int(r["open_time"]): float(r["open"]) for r in klines}
    lows = {int(r["open_time"]): float(r["low"]) for r in klines}
    rates = [(int(x["fundingTime"]) // HOUR * HOUR, float(x["fundingRate"]))
             for x in json.loads((root / "funding-api.json").read_text())]
    rows = []
    for year, (start, end) in YEARS.items():
        events: dict[str, dict[int, list[float]]] = {}
        for index, (time, rate) in enumerate(rates):
            entry = time + HOUR
            if not start <= time < end or entry not in opens:
                continue
            onset = rate < 0 and rates[index - 1][1] >= 0
            for horizon in (24, 72):
                exit_ = entry + horizon * HOUR
                if exit_ in opens:
                    move = opens[exit_] / opens[entry] - 1
                    for key in ("all", _level(rate)) + (("negative_onset",) if onset else ()):
                        events.setdefault(key, {24: [], 72: []})[horizon].append(move)
        study = {k: {f"{h}h_mean_bp": st.mean(v[h]) * 1e4 for h in (24, 72)} | {"events": len(v[24])}
                 for k, v in sorted(events.items())}
        for cost in (1, 2):
            side = 15 * cost / 1e4
            equity, peak, drawdown, busy, trades = 1.0, 1.0, 0.0, -1, []
            for time, rate in rates:
                entry, exit_ = time + HOUR, time + HOUR + 72 * HOUR
                if not start <= time < end or rate >= 0 or time < busy or exit_ not in opens or exit_ >= end:
                    continue
                gross = opens[exit_] / opens[entry] - 1
                funding = -sum(r for t, r in rates if entry <= t < exit_)
                net = gross + funding - 2 * side
                worst = min(lows[h] for h in range(entry, exit_, HOUR)) / opens[entry] - 1
                peak = max(peak, equity)
                drawdown = min(drawdown, equity * (1 + .5 * worst) / peak - 1)
                equity *= 1 + .5 * net
                trades.append(dict(entry_ms=entry, exit_ms=exit_, gross=gross, funding=funding, net=net))
                busy = exit_
            rows.append(dict(year=year, cost_multiplier=cost, event_study=study, trades=len(trades),
                             gross_mean_bp=st.mean(t["gross"] for t in trades) * 1e4,
                             net_mean_bp=st.mean(t["net"] for t in trades) * 1e4,
                             hit_rate=sum(t["net"] > 0 for t in trades) / len(trades),
                             total_return=equity - 1, approximate_max_drawdown=drawdown, trade_list=trades))
    OUTPUT.write_text(json.dumps(dict(schema="funding_sleeve_screen_v1", used_for_tuning=True,
        independent_validation=False, validation_tape_used=False, rows=rows), indent=2), encoding="utf-8")
    for row in rows:
        print(row["year"], row["cost_multiplier"], row["trades"], f"net={row['net_mean_bp']:.1f}bp",
              f"ret={row['total_return']*100:.2f}%", f"dd~{row['approximate_max_drawdown']*100:.2f}%")


if __name__ == "__main__":
    main()
