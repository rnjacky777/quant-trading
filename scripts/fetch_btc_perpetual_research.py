"""Download verified public futures inputs into a separate research cache."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from io import BytesIO, StringIO
import csv
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile


ROOT = Path("data/btc-perpetual-research")


def download_month(kind: str, month: str) -> dict:
    relative = f"data/futures/um/monthly/{kind}/BTCUSDT/4h/BTCUSDT-4h-{month}.zip"
    url = "https://data.binance.vision/" + relative
    target = ROOT / f"{kind}-{month}.zip"
    payload = target.read_bytes() if target.exists() else urlopen(url, timeout=25).read()
    checksum = urlopen(url+".CHECKSUM", timeout=25).read().decode().split()[0]
    if sha256(payload).hexdigest() != checksum:
        raise ValueError("archive checksum mismatch: " + url)
    target.write_bytes(payload)
    archive = ZipFile(BytesIO(payload))
    rows = list(csv.DictReader(StringIO(archive.read(archive.namelist()[0]).decode())))
    return dict(kind=kind, month=month, url=url, sha256=checksum, rows=rows)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    months = ["2023-12"] + [f"{year}-{month:02d}" for year in (2024, 2025) for month in range(1,13)]
    files = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = [pool.submit(download_month, kind, month) for kind in ("klines", "markPriceKlines") for month in months]
        for job in as_completed(jobs):
            files.append(job.result())
            if len(files) % 10 == 0:
                print("verified archives", len(files), "/",len(jobs),flush=True)
    funding_path = ROOT / "funding-api.json"
    if funding_path.exists():
        funding = json.loads(funding_path.read_text(encoding="utf-8"))
    else:
        funding = []
        cursor, end = 1701388800000, 1767225600000  # 2023-12-01 through 2026-01-01
        while cursor < end:
            url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime={cursor}&endTime={end-1}&limit=1000"
            batch = json.loads(urlopen(url,timeout=25).read())
            if not batch:
                if funding and end-int(funding[-1]["fundingTime"]) <= 8*60*60*1000:
                    break
                raise ValueError("funding history ended before requested coverage")
            funding.extend(batch)
            cursor = int(batch[-1]["fundingTime"])+1
        funding_path.write_text(json.dumps(funding),encoding="utf-8")
    manifest = []
    for kind in ("klines","markPriceKlines"):
        data = [row for item in files if item["kind"] == kind for row in item["rows"]]
        data.sort(key=lambda row:int(row["open_time"]))
        times = [int(row["open_time"]) for row in data]
        if times != list(range(1701388800000,1767225600000,14400000)):
            raise ValueError("missing or duplicate futures bars: " + kind)
        (ROOT / f"{kind}.json").write_text(json.dumps(data),encoding="utf-8")
    times = [int(row["fundingTime"]) for row in funding]
    if len(times) != len(set(times)) or times != sorted(times):
        raise ValueError("duplicate or disorder in funding history")
    expected_funding = list(range(1701388800000,1767225600000,8*60*60*1000))
    if len(times) != len(expected_funding) or any(abs(actual-expected)>1000 for actual,expected in zip(times,expected_funding)):
        raise ValueError("funding events do not cover the full expected 8h schedule")
    if any(not row.get("markPrice") or float(row["markPrice"]) <= 0 for row in funding):
        raise ValueError("funding record lacks its actual mark price")
    # Record actual spacing rather than manufacture missing funding events.
    for item in files:
        manifest.append({key:value for key,value in item.items() if key!="rows"})
    (ROOT / "manifest.json").write_text(json.dumps(dict(files=manifest,funding_count=len(funding),
        funding_source="https://fapi.binance.com/fapi/v1/fundingRate",funding_sha256=sha256(funding_path.read_bytes()).hexdigest(),
        historical_margin_brackets="NOT AVAILABLE; research stress assumptions required"),indent=2),encoding="utf-8")
    print("saved futures tape, mark prices and",len(funding),"actual funding records",flush=True)


if __name__ == "__main__":
    main()
