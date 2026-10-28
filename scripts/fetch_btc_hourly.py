"""Import verified Binance spot 1h monthly data for 2024/25 plus warmup."""
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
from time import sleep
from urllib.request import urlopen
from zipfile import ZipFile

from app.data.models import Candle
from app.data.repository import CandleRepository


CACHE = Path("data/btc-spot-1h")


def parse_archive(payload: bytes) -> list[Candle]:
    with ZipFile(BytesIO(payload)) as archive:
        names = archive.namelist()
        if len(names) != 1 or not names[0].endswith(".csv"):
            raise ValueError("unexpected archive contents")
        rows = list(csv.reader(StringIO(archive.read(names[0]).decode("utf-8"))))
    candles = []
    for row in rows:
        timestamp = int(row[0])
        if timestamp >= 10**14:
            if timestamp % 1000:
                raise ValueError("non-millisecond candle timestamp")
            timestamp //= 1000
        if timestamp % 3600000:
            raise ValueError("unaligned hourly timestamp")
        candles.append(Candle("binance", "BTC/USDT", "1h", timestamp, *map(float, row[1:6])))
    return candles


def request_bytes(url: str) -> bytes:
    for attempt in range(3):
        try:
            with urlopen(url, timeout=30) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            sleep(attempt + 1)
    raise RuntimeError("unreachable")


def fetch_month(month: str) -> tuple[dict, list[Candle]]:
    name = f"BTCUSDT-1h-{month}.zip"
    url = f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/{name}"
    target = CACHE / name
    payload = target.read_bytes() if target.exists() else request_bytes(url)
    expected = request_bytes(url + ".CHECKSUM").decode().split()[0]
    actual = sha256(payload).hexdigest()
    if actual != expected:
        raise ValueError(f"checksum mismatch: {month}")
    candles = parse_archive(payload)
    year, number = map(int, month.split("-"))
    start = int(datetime(year, number, 1, tzinfo=timezone.utc).timestamp() * 1000)
    end = int(datetime(year + (number == 12), number % 12 + 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    if [c.timestamp_ms for c in candles] != list(range(start, end, 3600000)):
        raise ValueError(f"missing, duplicated or out-of-order candles: {month}")
    target.write_bytes(payload)
    return dict(month=month, url=url, sha256=actual, candles=len(candles)), candles


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    months = ["2023-12"] + [f"{year}-{month:02d}" for year in (2024, 2025) for month in range(1, 13)]
    # Validate all inputs before mutating the market database.
    with ThreadPoolExecutor(max_workers=4) as pool:
        batches = list(pool.map(fetch_month, months))
    candles = [c for _, batch in batches for c in batch]
    if [c.timestamp_ms for c in candles] != list(range(1701388800000, 1767225600000, 3600000)):
        raise ValueError("incomplete combined hourly dataset")
    repo = CandleRepository(Path("data/market.sqlite3"))
    existing = repo.list_range("binance", "BTC/USDT", "1h", 1701388800000, 1767225600000)
    by_time = {c.timestamp_ms: c for c in candles}
    if any(by_time[c.timestamp_ms] != c for c in existing):
        raise ValueError("existing data differs; refusing to overwrite evidence")
    existing_times = {c.timestamp_ms for c in existing}
    repo.upsert([c for c in candles if c.timestamp_ms not in existing_times])
    saved = repo.list_range("binance", "BTC/USDT", "1h", 1701388800000, 1767225600000)
    if saved != candles:
        raise ValueError("database verification failed")
    counts = {str(year): sum(datetime.fromtimestamp(c.timestamp_ms/1000, timezone.utc).year == year for c in saved) for year in (2023, 2024, 2025)}
    manifest = dict(exchange="binance", market="spot", symbol="BTC/USDT", timeframe="1h",
                    files=[item for item, _ in batches], counts=counts, total=len(saved),
                    missing=0, duplicates=0, timestamp_unit="milliseconds; 2025 archive microseconds normalized",
                    until_exclusive="2026-01-01T00:00:00Z", first="2023-12-01T00:00:00Z", last="2025-12-31T23:00:00Z")
    (CACHE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(dict(counts=counts, total=len(saved), missing=0, duplicates=0)))


if __name__ == "__main__":
    main()
