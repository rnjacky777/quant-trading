"""Daily perp klines for every multi-coin universe member, 2021-10..2025-12 (design: 2026-10-30-multi-coin-trend-design.md).

Reuses the checksum-verified archive cache of the multi-coin carry fetcher; whole missing days are refilled
from daily archives. Prints counts only.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path

from scripts.fetch_multi_coin_carry import ROOT as CARRY_ROOT, get, months_available, ms

ROOT = Path("data/multi-coin-trend")
MONTHS = [f"{y}-{m:02d}" for y in range(2021, 2026) for m in range(1, 13) if f"{y}-{m:02d}" >= "2021-10"]
DAY_MS = 86400000


def main() -> None:
    universe = json.loads((CARRY_ROOT / "universe.json").read_text(encoding="utf-8"))["universe"]
    members = sorted({p for u in universe.values() for p in u})
    with ThreadPoolExecutor(max_workers=16) as pool:
        listed = dict(zip(members, pool.map(lambda p: months_available(f"data/futures/um/monthly/klines/{p}/1d/"), members)))
        jobs = [(p, m) for p in members for m in MONTHS if m in listed[p]]
        monthly = list(pool.map(lambda j: (j[0], get(f"futures/um/monthly/klines/{j[0]}/1d/{j[0]}-1d-{j[1]}.zip") or []), jobs))
        bars: dict[str, dict[int, list[float]]] = {}
        for perp, rows in monthly:
            bars.setdefault(perp, {}).update({ms(r[0]): [float(x) for x in r[1:5]] for r in rows})
        fills = []
        for perp, days in bars.items():
            if days:
                fills += [(perp, t) for t in range(min(days), max(days), DAY_MS) if t not in days]
        filled = list(pool.map(lambda j: (j[0], get("futures/um/daily/klines/{p}/1d/{p}-1d-{d}.zip".format(
            p=j[0], d=datetime.fromtimestamp(j[1] / 1000, timezone.utc).strftime("%Y-%m-%d"))) or []), fills))
    for perp, rows in filled:
        bars[perp].update({ms(r[0]): [float(x) for x in r[1:5]] for r in rows})
    (ROOT / "daily").mkdir(parents=True, exist_ok=True)
    gaps = 0
    for perp, days in bars.items():
        (ROOT / "daily" / f"{perp}.json").write_text(json.dumps(sorted(days.items())), encoding="utf-8")
        if days:
            gaps += sum(t not in days for t in range(min(days), max(days), DAY_MS))
    print("symbols", len(bars), "monthly files", len(jobs), "daily fill requests", len(fills), "remaining interior gaps", gaps)


if __name__ == "__main__":
    main()
