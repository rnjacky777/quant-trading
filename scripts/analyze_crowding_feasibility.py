"""Preregistered crowding feasibility (docs/research/2026-10-29-crowding-feasibility-design.md).

Event study only: causal features at hour T from metrics stamped <= T-5min and
completed bars; forward 24h open-to-open returns are diagnostics, never features.
"""
import csv
from datetime import datetime, timezone
from io import StringIO
import json
from math import log, sqrt
from pathlib import Path
from statistics import mean, pstdev
from zipfile import ZipFile

from scripts.research_risk_budget import late_inputs
from scripts.validate_baseline_2022_2023 import load_inputs

H = 3600000
OUTPUT = Path("data/crowding-feasibility.json")
COST = .002
WINDOW = 720
START = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def metrics() -> dict[int, dict]:
    rows = {}
    for path in sorted(Path("data/btc-perpetual-metrics").glob("*.zip")):
        with ZipFile(path) as z:
            for r in csv.DictReader(StringIO(z.read(z.namelist()[0]).decode())):
                t = int(datetime.strptime(r["create_time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp() * 1000)
                def num(key: str) -> float | None:
                    return float(r[key]) if r[key] not in ("", None) else None
                rows[t] = dict(oi=num("sum_open_interest"), top=num("count_toptrader_long_short_ratio"),
                               taker=num("sum_taker_long_short_vol_ratio"))
    return rows


def zscores(values: dict[int, float | None], hours: list[int]) -> dict[int, float]:
    out, history = {}, []
    for t in hours:
        v = values.get(t)
        valid = [x for x in history[-WINDOW:] if x is not None]
        if v is not None and len(valid) >= 600:
            sd = pstdev(valid)
            if sd > 0:
                out[t] = (v - mean(valid)) / sd
        history.append(v)
    return out


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite research evidence")
    m = metrics()
    early, late = load_inputs(), late_inputs()
    bars = {c.timestamp_ms: c for c in early[0] + late[0]}
    hours = list(range(START - 40 * 24 * H, END, H))
    # Value known at decision hour T: the 5-minute sample stamped T-5min.
    sample = {t: m.get(t - 300000) for t in hours}
    oi_change, top24, taker24 = {}, {}, {}
    for t in hours:
        now, then = sample[t], sample.get(t - 24 * H)
        if now and then and now["oi"] and then["oi"]:
            oi_change[t] = log(now["oi"] / then["oi"])
        for key, target in (("top", top24), ("taker", taker24)):
            window = [sample.get(t - k * H) for k in range(24)]
            values = [s[key] for s in window if s and s[key] is not None]
            target[t] = mean(values) if len(values) >= 20 else None
    z = dict(oi=zscores(oi_change, hours), top=zscores(top24, hours), taker=zscores(taker24, hours))
    coverage = {k: sum(1 for t in hours if t >= START and t in v) / sum(1 for t in hours if t >= START) for k, v in z.items()}

    def price_change(t: int) -> float | None:
        a, b = bars.get(t - H), bars.get(t - 25 * H)
        return a.close / b.close - 1 if a and b else None

    def forward(t: int) -> float | None:
        a, b = bars.get(t), bars.get(t + 24 * H)
        return b.open / a.open - 1 if a and b else None

    rules = {
        "crowded_long_oi": (lambda t: z["oi"].get(t, 0) > 2 and (price_change(t) or 0) > 0, -1),
        "crowded_short_oi": (lambda t: z["oi"].get(t, 0) > 2 and (price_change(t) or 0) < 0, 1),
        "top_ratio_high": (lambda t: z["top"].get(t, 0) > 2, -1),
        "top_ratio_low": (lambda t: z["top"].get(t, 0) < -2, 1),
        "taker_buy_heavy": (lambda t: z["taker"].get(t, 0) > 2, -1),
        "taker_sell_heavy": (lambda t: z["taker"].get(t, 0) < -2, 1),
    }
    results = {}
    for name, (condition, direction) in rules.items():
        events, blocked_until = [], -1
        for t in range(START, END - 24 * H, H):
            if t < blocked_until or not condition(t):
                continue
            r = forward(t)
            if r is None:
                continue
            events.append(dict(t=t, year=datetime.fromtimestamp(t / 1000, timezone.utc).year, net=direction * r - COST))
            blocked_until = t + 24 * H
        per_year = {}
        for y in range(2022, 2026):
            xs = [e["net"] for e in events if e["year"] == y]
            per_year[y] = dict(n=len(xs), mean_net_bps=mean(xs) * 1e4 if xs else None)
        xs = [e["net"] for e in events]
        t_stat = mean(xs) / (pstdev(xs) / sqrt(len(xs))) if len(xs) > 1 and pstdev(xs) > 0 else None
        passed = (bool(xs) and mean(xs) * 1e4 >= 30 and
                  sum(1 for v in per_year.values() if v["mean_net_bps"] is not None and v["mean_net_bps"] > 0) >= 3 and
                  all(v["n"] >= 15 for v in per_year.values()))
        results[name] = dict(trade_direction=direction, events=len(xs), mean_net_bps=mean(xs) * 1e4 if xs else None,
                             t_stat=t_stat, per_year=per_year, feasible=passed)
        yrs = " ".join(f"{y}:{v['n']}/{v['mean_net_bps']:+.0f}" if v["mean_net_bps"] is not None else f"{y}:0" for y, v in per_year.items())
        print(f"{name:18s} dir={direction:+d} n={len(xs):4d} mean_net={results[name]['mean_net_bps'] or 0:+7.1f}bps "
              f"t={t_stat or 0:+.2f} | {yrs} | feasible={passed}")
    OUTPUT.write_text(json.dumps(dict(design="docs/research/2026-10-29-crowding-feasibility-design.md",
        cost_round_trip=COST, coverage=coverage, results=results, tuning_evidence=True), indent=1), encoding="utf-8")
    print("coverage", {k: f"{v:.1%}" for k, v in coverage.items()})


if __name__ == "__main__":
    main()
