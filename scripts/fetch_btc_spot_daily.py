"""BTCUSDT spot daily klines 2021-10..2025-12 (design: 2026-10-30-btc-trend-filter-design.md).

Starts after the sealed period (ends 2021-09-30). Checksums verified via the shared archive cache; prints counts only.
"""
import json
from pathlib import Path

from scripts.fetch_multi_coin_carry import get, ms

OUTPUT = Path("data/btc-spot-1d/klines.json")
MONTHS = [f"{y}-{m:02d}" for y in range(2021, 2026) for m in range(1, 13) if f"{y}-{m:02d}" >= "2021-10"]
DAY_MS = 86400000


def main() -> None:
    bars = {}
    for month in MONTHS:
        for r in get(f"spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-{month}.zip") or []:
            bars[ms(r[0])] = [float(x) for x in r[1:5]]
    days = sorted(bars)
    gaps = sum(t not in bars for t in range(days[0], days[-1], DAY_MS))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(sorted(bars.items())), encoding="utf-8")
    print("days", len(days), "gaps", gaps)


if __name__ == "__main__":
    main()
