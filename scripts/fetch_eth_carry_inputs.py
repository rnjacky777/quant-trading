"""Checksum-verified ETHUSDT perpetual klines/marks, actual funding, and spot klines for 2022-2025."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from scripts.fetch_btc_hourly import parse_archive, request_bytes

PERP = Path("data/eth-perpetual-1h")
SPOT = Path("data/eth-spot-1h")
COLUMNS = ("open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
           "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore")
START = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
MONTHS = [f"{y}-{m:02d}" for y in range(2022, 2026) for m in range(1, 13)]


def verified(url: str, target: Path) -> bytes:
    payload = target.read_bytes() if target.exists() else request_bytes(url)
    if sha256(payload).hexdigest() != request_bytes(url + ".CHECKSUM").decode().split()[0]:
        raise ValueError("checksum mismatch: " + url)
    target.write_bytes(payload)
    return payload


def rows(payload: bytes) -> list[dict]:
    with ZipFile(BytesIO(payload)) as archive:
        lines = archive.read(archive.namelist()[0]).decode().splitlines()
    data = lines[1:] if lines and lines[0].startswith("open_time") else lines
    return [dict(zip(COLUMNS, line.split(","))) for line in data if line]


def perp_month(job: tuple[str, str]) -> list[dict]:
    kind, month = job
    url = f"https://data.binance.vision/data/futures/um/monthly/{kind}/ETHUSDT/1h/ETHUSDT-1h-{month}.zip"
    return rows(verified(url, PERP / f"{kind}-{month}.zip"))


def perp_day(job: tuple[str, str]) -> list[dict]:
    kind, day = job
    url = f"https://data.binance.vision/data/futures/um/daily/{kind}/ETHUSDT/1h/ETHUSDT-1h-{day}.zip"
    return rows(verified(url, PERP / f"{kind}-{day}.zip"))


def spot_month(month: str) -> list:
    url = f"https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1h/ETHUSDT-1h-{month}.zip"
    return parse_archive(verified(url, SPOT / f"ETHUSDT-1h-{month}.zip"))


def funding() -> list[dict]:
    out, cursor = [], START
    while cursor < END:
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol=ETHUSDT&startTime={cursor}&endTime={END - 1}&limit=1000"
        batch = json.loads(urlopen(url, timeout=25).read())
        if not batch:
            break
        out += batch
        cursor = int(batch[-1]["fundingTime"]) + 1
    return out


def main() -> None:
    PERP.mkdir(parents=True, exist_ok=True)
    SPOT.mkdir(parents=True, exist_ok=True)
    expected = list(range(START, END, 3600000))
    summary = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for kind in ("klines", "markPriceKlines"):
            merged = {int(r["open_time"]): r for batch in pool.map(perp_month, [(kind, m) for m in MONTHS]) for r in batch}
            missing_days = sorted({datetime.fromtimestamp(t / 1000, timezone.utc).date().isoformat()
                                   for t in expected if t not in merged})
            for batch in pool.map(perp_day, [(kind, d) for d in missing_days]):
                merged.update({int(r["open_time"]): r for r in batch})
            gaps = [t for t in expected if t not in merged]
            if gaps:
                raise ValueError(f"{kind}: {len(gaps)} hours missing after daily fill, first {gaps[:3]}")
            (PERP / f"{kind}.json").write_text(json.dumps([merged[t] for t in expected]), encoding="utf-8")
            summary[kind] = dict(hours=len(expected), daily_filled_days=missing_days)
        spot = sorted((c for batch in pool.map(spot_month, MONTHS) for c in batch), key=lambda c: c.timestamp_ms)
    spot_gaps = sorted(set(expected) - {c.timestamp_ms for c in spot})
    summary["spot"] = dict(hours=len(spot), missing_hours=spot_gaps)
    events = funding()
    (PERP / "funding-api.json").write_text(json.dumps(events), encoding="utf-8")
    summary["funding"] = dict(events=len(events), missing_mark=sum(1 for f in events if not f.get("markPrice")))
    (PERP / "manifest.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({k: {kk: (vv if not isinstance(vv, list) else len(vv)) for kk, vv in v.items()} for k, v in summary.items()}))
    if spot_gaps:
        print("spot gaps (UTC):", [datetime.fromtimestamp(t / 1000, timezone.utc).isoformat() for t in spot_gaps])


if __name__ == "__main__":
    main()
