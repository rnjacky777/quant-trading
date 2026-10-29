"""Checksum-verified Binance spot BTCUSDT 1h archives for 2022-01..2023-11.

Kept in a separate directory; the existing spot manifest and market database
are not modified.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from scripts.fetch_btc_hourly import parse_archive, request_bytes

CACHE = Path("data/btc-spot-1h-2022-2023")
# Binance spot halted trading 2023-03-24 (no 13:00 UTC candle exists); see the design amendment.
KNOWN_OUTAGES = {1679662800000}
MONTHS = [f"{y}-{m:02d}" for y in (2022, 2023) for m in range(1, 13) if (y, m) != (2023, 12)]


def fetch_month(month: str) -> dict:
    name = f"BTCUSDT-1h-{month}.zip"
    url = f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/{name}"
    target = CACHE / name
    payload = target.read_bytes() if target.exists() else request_bytes(url)
    expected = request_bytes(url + ".CHECKSUM").decode().split()[0]
    if sha256(payload).hexdigest() != expected:
        raise ValueError(f"checksum mismatch: {month}")
    candles = parse_archive(payload)
    year, number = map(int, month.split("-"))
    start = int(datetime(year, number, 1, tzinfo=timezone.utc).timestamp() * 1000)
    end = int(datetime(year + (number == 12), number % 12 + 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    if [c.timestamp_ms for c in candles] != [t for t in range(start, end, 3600000) if t not in KNOWN_OUTAGES]:
        raise ValueError(f"missing, duplicated or out-of-order candles: {month}")
    target.write_bytes(payload)
    return dict(month=month, url=url, sha256=expected, candles=len(candles))


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    files = [fetch_month(m) for m in MONTHS]
    manifest = dict(exchange="binance", market="spot", symbol="BTC/USDT", timeframe="1h", files=files,
                    total=sum(f["candles"] for f in files), first="2022-01-01T00:00:00Z",
                    until_exclusive="2023-12-01T00:00:00Z", known_outage_hours_ms=sorted(KNOWN_OUTAGES))
    (CACHE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(dict(months=len(files), total=manifest["total"])))


if __name__ == "__main__":
    main()
