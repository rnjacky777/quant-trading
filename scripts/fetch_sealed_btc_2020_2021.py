"""Download and seal BTC perpetual + spot data for 2020-01..2021-09 (sealed validation set).

Binance perpetual archives start 2020-01, so January 2020 is warmup only.

Integrity checks only (checksums, hourly continuity, funding schedule). Prints
counts and hashes, never prices or returns. Research code must not read it
outside a preregistered, logged evaluation (AGENTS §1 data roles).
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from scripts.fetch_btc_hourly import request_bytes

ROOT = Path("data/sealed-btc-2020-2021")
MONTHS = [f"{y}-{m:02d}" for y in (2020, 2021) for m in range(1, 13) if (y, m) <= (2021, 9)]
START = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2021, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
SOURCES = {
    "perp_klines": "https://data.binance.vision/data/futures/um/{freq}/klines/BTCUSDT/1h/BTCUSDT-1h-{when}.zip",
    "perp_marks": "https://data.binance.vision/data/futures/um/{freq}/markPriceKlines/BTCUSDT/1h/BTCUSDT-1h-{when}.zip",
    "spot_klines": "https://data.binance.vision/data/spot/{freq}/klines/BTCUSDT/1h/BTCUSDT-1h-{when}.zip",
}


def fetch(job: tuple[str, str, str]) -> dict:
    kind, freq, when = job
    url = SOURCES[kind].format(freq=freq, when=when)
    target = ROOT / kind / f"{when}.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = target.read_bytes() if target.exists() else request_bytes(url)
    expected = request_bytes(url + ".CHECKSUM").decode().split()[0]
    if sha256(payload).hexdigest() != expected:
        raise ValueError("checksum mismatch: " + url)
    target.write_bytes(payload)
    with ZipFile(BytesIO(payload)) as archive:
        lines = archive.read(archive.namelist()[0]).decode().splitlines()
    stamps = []
    for line in lines:
        head = line.split(",")[0]
        if head.isdigit():
            t = int(head)
            stamps.append(t // 1000 if t >= 10 ** 14 else t)
    return dict(kind=kind, when=when, url=url, sha256=expected, stamps=stamps)


def main() -> None:
    expected = set(range(START, END, 3600000))
    report = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        files = list(pool.map(fetch, [(k, "monthly", m) for k in SOURCES for m in MONTHS]))
        for kind in SOURCES:
            got = {t for f in files if f["kind"] == kind for t in f["stamps"]}
            missing = sorted(expected - got)
            days = sorted({datetime.fromtimestamp(t / 1000, timezone.utc).date().isoformat() for t in missing})
            if days:
                try:
                    extra = list(pool.map(fetch, [(kind, "daily", d) for d in days]))
                    files += extra
                    got |= {t for f in extra for t in f["stamps"]}
                except Exception as exc:  # noqa: BLE001 - recorded, never hidden
                    report[f"{kind}_daily_fill_error"] = str(exc)
            report[kind] = dict(hours=len(got & expected), missing_hours=sorted(expected - got))
    funding, cursor = [], START
    while cursor < END:
        batch = json.loads(urlopen(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime={cursor}"
                                   f"&endTime={END - 1}&limit=1000", timeout=25).read())
        if not batch:
            break
        funding += batch
        cursor = int(batch[-1]["fundingTime"]) + 1
    payload = json.dumps(funding).encode()
    (ROOT / "funding-api.json").write_bytes(payload)
    report["funding"] = dict(events=len(funding), missing_mark=sum(1 for f in funding if not f.get("markPrice")),
                             sha256=sha256(payload).hexdigest())
    manifest = dict(status="sealed", sealed_utc=datetime.now(timezone.utc).isoformat(), period="2020-01-01..2021-09-30; 2020-01 is warmup, evaluation 2020-02-01..2021-09-30",
                    rule="integrity only; evaluate a candidate only after preregistration and a log entry",
                    files=[{k: v for k, v in f.items() if k != "stamps"} for f in files], integrity=report)
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({k: (dict(hours=v["hours"], missing=len(v["missing_hours"])) if "hours" in v else v)
                      for k, v in report.items() if isinstance(v, dict)}))
    for kind in SOURCES:
        gaps = report[kind]["missing_hours"]
        if gaps:
            print(kind, "missing hours (UTC):", [datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m-%d %H:00") for t in gaps][:20],
                  "total", len(gaps))


if __name__ == "__main__":
    main()
