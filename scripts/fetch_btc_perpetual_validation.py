"""Preregistered 2022/2023 validation tape; integrity checks only, no statistics."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
from zipfile import ZipFile

from scripts.fetch_btc_hourly import request_bytes
from scripts.fetch_btc_perpetual_hourly import fetch_month
import scripts.fetch_btc_perpetual_hourly as hourly


ROOT = Path("data/btc-perpetual-validation-1h")
START_MS = 1633046400000  # 2021-10-01 warmup start
END_MS = 1701388800000  # 2023-12-01; later hours already exist in the tuning tape


COLUMNS = ("open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
           "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore")


def fetch_archive(job: tuple[str, str]) -> dict:
    """Older monthly archives omit the CSV header; name columns explicitly."""
    result = fetch_month(job)
    with ZipFile(ROOT / f"{job[0]}-{job[1]}.zip") as archive:
        lines = archive.read(archive.namelist()[0]).decode().splitlines()
    data = lines[1:] if lines[0].startswith("open_time") else lines
    result["rows"] = [dict(zip(COLUMNS, line.split(","))) for line in data if line]
    return result


def fetch_daily_marks(day: str) -> dict:
    """Monthly mark archives omit some whole days; the daily archive fills them."""
    url = f"https://data.binance.vision/data/futures/um/daily/markPriceKlines/BTCUSDT/1h/BTCUSDT-1h-{day}.zip"
    target = ROOT / f"markPriceKlines-{day}.zip"
    payload = target.read_bytes() if target.exists() else request_bytes(url)
    if sha256(payload).hexdigest() != request_bytes(url + ".CHECKSUM").decode().split()[0]:
        raise ValueError("checksum mismatch: " + url)
    target.write_bytes(payload)
    with ZipFile(target) as archive:
        lines = archive.read(archive.namelist()[0]).decode().splitlines()
    data = lines[1:] if lines[0].startswith("open_time") else lines
    return dict(kind="markPriceKlines", month=day, url=url, sha256=sha256(payload).hexdigest(),
                rows=[dict(zip(COLUMNS, line.split(","))) for line in data if line])


def fetch_funding() -> list[dict]:
    path = ROOT / "funding-api.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    funding, cursor = [], START_MS
    while cursor < END_MS:
        url = ("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT"
               f"&startTime={cursor}&endTime={END_MS-1}&limit=1000")
        batch = json.loads(request_bytes(url))
        if not batch:
            break
        funding.extend(batch)
        cursor = int(batch[-1]["fundingTime"]) + 1
    path.write_text(json.dumps(funding), encoding="utf-8")
    return funding


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    hourly.ROOT = ROOT
    months = [f"2021-{m:02d}" for m in (10, 11, 12)] + [f"{y}-{m:02d}" for y in (2022, 2023) for m in range(1, 13)][:-1]
    with ThreadPoolExecutor(max_workers=6) as pool:
        files = list(pool.map(fetch_archive,[(k, m) for k in ("klines", "markPriceKlines") for m in months]))
        files += list(pool.map(fetch_daily_marks, ("2022-07-31", "2022-10-02", "2023-02-24")))
    expected = list(range(START_MS, END_MS, 3600000))
    for kind in ("klines", "markPriceKlines"):
        rows = sorted([r for f in files if f["kind"] == kind for r in f["rows"]], key=lambda r: int(r["open_time"]))
        if [int(r["open_time"]) for r in rows] != expected:
            raise ValueError("incomplete or duplicated hourly " + kind)
        if any(not all(isfinite(float(r[k])) and float(r[k]) > 0 for k in ("open", "high", "low", "close")) for r in rows):
            raise ValueError("invalid prices in " + kind)
        (ROOT / f"{kind}.json").write_text(json.dumps(rows), encoding="utf-8")
    funding = fetch_funding()
    times = [int(f["fundingTime"]) for f in funding]
    schedule = list(range(START_MS, END_MS, 28800000))
    if times != sorted(set(times)) or len(times) != len(schedule) or any(abs(a - b) > 1000 for a, b in zip(times, schedule)):
        raise ValueError("incomplete funding history")
    if any(not isfinite(float(f["fundingRate"])) for f in funding):
        raise ValueError("invalid funding rate")
    # Older API records may omit markPrice; count them instead of inventing values.
    missing_mark = sum(not f.get("markPrice") or float(f["markPrice"]) <= 0 for f in funding)
    payload = (ROOT / "funding-api.json").read_bytes()
    manifest = dict(files=[{k: v for k, v in f.items() if k != "rows"} for f in files],
        candles_per_kind=len(expected), funding_count=len(funding), funding_missing_mark_price=missing_mark,
        funding_sha256=sha256(payload).hexdigest(), funding_source="https://fapi.binance.com/fapi/v1/fundingRate",
        since="2021-10-01T00:00:00Z", until_exclusive="2023-12-01T00:00:00Z",
        continuation="2023-12 onward comes from data/btc-perpetual-1h",
        preregistration="data/validation-preregistration.json")
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Verified {len(files)} archives; {len(expected)} hourly bars and marks; "
          f"{len(funding)} funding events; {missing_mark} without mark price")


if __name__ == "__main__":
    main()
