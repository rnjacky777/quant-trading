"""Checksum-verified Binance USD-M BTCUSDT daily metrics (5-minute OI and ratios), 2021-12..2025-12."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path

from scripts.fetch_btc_hourly import request_bytes

CACHE = Path("data/btc-perpetual-metrics")
BASE = "https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT"


def days() -> list[str]:
    start, end = date(2021, 12, 1), date(2025, 12, 31)
    return [(start + timedelta(n)).isoformat() for n in range((end - start).days + 1)]


def fetch(day: str) -> dict:
    name = f"BTCUSDT-metrics-{day}.zip"
    target = CACHE / name
    payload = target.read_bytes() if target.exists() else request_bytes(f"{BASE}/{name}")
    expected = request_bytes(f"{BASE}/{name}.CHECKSUM").decode().split()[0]
    if sha256(payload).hexdigest() != expected:
        raise ValueError(f"checksum mismatch: {day}")
    target.write_bytes(payload)
    return dict(day=day, sha256=expected)


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        files = list(pool.map(fetch, days()))
    (CACHE / "manifest.json").write_text(json.dumps(dict(source=BASE, files=files), indent=1), encoding="utf-8")
    print(json.dumps(dict(days=len(files))))


if __name__ == "__main__":
    main()
