"""Verified hourly futures tape and marks, isolated from spot market data."""
from concurrent.futures import ThreadPoolExecutor
import csv
from hashlib import sha256
from io import BytesIO, StringIO
import json
from math import isfinite
from pathlib import Path
from zipfile import ZipFile

from app.data.models import Candle, MarkPriceCandle
from scripts.fetch_btc_hourly import request_bytes


ROOT = Path("data/btc-perpetual-1h")


def fetch_month(job: tuple[str, str]) -> dict:
    kind, month = job
    url = f"https://data.binance.vision/data/futures/um/monthly/{kind}/BTCUSDT/1h/BTCUSDT-1h-{month}.zip"
    target = ROOT / f"{kind}-{month}.zip"
    payload = target.read_bytes() if target.exists() else request_bytes(url)
    expected = request_bytes(url+".CHECKSUM").decode().split()[0]
    if sha256(payload).hexdigest() != expected:
        raise ValueError("checksum mismatch: "+url)
    with ZipFile(BytesIO(payload)) as archive:
        if len(archive.namelist()) != 1:
            raise ValueError("unexpected archive contents")
        rows = list(csv.DictReader(StringIO(archive.read(archive.namelist()[0]).decode())))
    target.write_bytes(payload)
    return dict(kind=kind, month=month, url=url, sha256=expected, rows=rows)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    months = ["2023-12"]+[f"{y}-{m:02d}" for y in (2024,2025) for m in range(1,13)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        files = list(pool.map(fetch_month, [(k,m) for k in ("klines","markPriceKlines") for m in months]))
    expected = list(range(1701388800000,1767225600000,3600000))
    for kind in ("klines","markPriceKlines"):
        rows = sorted([r for f in files if f["kind"]==kind for r in f["rows"]], key=lambda r:int(r["open_time"]))
        if [int(r["open_time"]) for r in rows] != expected:
            raise ValueError("incomplete or duplicated hourly "+kind)
        for r in rows:
            prices=[float(r[k]) for k in ("open","high","low","close")]
            if kind=="klines":
                Candle("binance-usdm","BTC/USDT","1h",int(r["open_time"]),*prices,float(r["volume"]))
            else:
                MarkPriceCandle("binance-usdm","BTC/USDT",int(r["open_time"]),*prices,timeframe="1h")
        (ROOT/f"{kind}.json").write_text(json.dumps(rows),encoding="utf-8")
    # Reuse actual, previously downloaded funding events, never interpolate.
    source = Path("data/btc-perpetual-research/funding-api.json")
    payload = source.read_bytes()
    funding = json.loads(payload)
    times=[int(f["fundingTime"]) for f in funding]
    schedule=list(range(1701388800000,1767225600000,28800000))
    if len(times)!=len(schedule) or times!=sorted(set(times)) or any(abs(a-b)>1000 for a,b in zip(times,schedule)):
        raise ValueError("incomplete funding history")
    if any(not isfinite(float(f['fundingRate'])) or not isfinite(float(f['markPrice'])) or float(f['markPrice'])<=0 for f in funding):
        raise ValueError("invalid funding inputs")
    (ROOT/"funding-api.json").write_bytes(payload)
    manifest=dict(files=[{k:v for k,v in f.items() if k!='rows'} for f in files],
        candles_per_kind=len(expected),funding_count=len(funding),funding_sha256=sha256(payload).hexdigest(),
        funding_source="https://fapi.binance.com/fapi/v1/fundingRate",reused_funding_cache=str(source),
        since="2023-12-01T00:00:00Z",until_exclusive="2026-01-01T00:00:00Z",
        historical_margin_brackets="UNVERIFIED: research must state assumed margin rates")
    (ROOT/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(f"Verified {len(files)} archives; {len(expected)} hourly bars and marks; {len(funding)} actual funding events")


if __name__=="__main__":
    main()
