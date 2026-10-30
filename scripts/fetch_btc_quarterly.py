"""Download BTCUSDT quarterly delivery 1h klines and mark klines for 2022-01..2025-12 (basis-carry research).

Checksums are verified; prints counts only. 2021 data falls in the sealed period and is not fetched.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from scripts.fetch_btc_hourly import request_bytes

ROOT = Path("data/btc-quarterly-1h")
CONTRACTS = ("220325", "220624", "220930", "221230", "230331", "230630", "230929", "231229",
             "240329", "240628", "240927", "241227", "250328", "250627", "250926", "251226", "260327")
MONTHS = [f"{y}-{m:02d}" for y in range(2022, 2026) for m in range(1, 13)]
URL = "https://data.binance.vision/data/futures/um/{freq}/{kind}/BTCUSDT_{c}/1h/BTCUSDT_{c}-1h-{when}.zip"


def delivery_ms(contract: str) -> int:
    """Binance USDT-M quarterly contracts deliver at 08:00 UTC on the date in the symbol."""
    return int(datetime.strptime("20" + contract, "%Y%m%d").replace(hour=8, tzinfo=timezone.utc).timestamp() * 1000)


def fetch(job: tuple[str, str, str]) -> dict | None:
    kind, contract, when = job
    url = URL.format(freq="daily" if len(when) == 10 else "monthly", kind=kind, c=contract, when=when)
    target = ROOT / contract / kind / f"{when}.zip"
    try:
        payload = target.read_bytes() if target.exists() else request_bytes(url)
    except Exception:  # noqa: BLE001 - month outside the contract's listing window
        return None
    expected = request_bytes(url + ".CHECKSUM").decode().split()[0]
    if sha256(payload).hexdigest() != expected:
        raise ValueError("checksum mismatch: " + url)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    with ZipFile(BytesIO(payload)) as archive:
        lines = archive.read(archive.namelist()[0]).decode().splitlines()
    rows = [line.split(",") for line in lines if line.split(",")[0].isdigit()]
    return dict(kind=kind, contract=contract, when=when, url=url, sha256=expected,
                rows=[dict(open_time=int(r[0]), open=float(r[1]), high=float(r[2]), low=float(r[3]),
                           close=float(r[4]), volume=float(r[5])) for r in rows])


def main() -> None:
    jobs = [(k, c, m) for k in ("klines", "markPriceKlines") for c in CONTRACTS for m in MONTHS
            if m <= datetime.fromtimestamp(delivery_ms(c) / 1000, timezone.utc).strftime("%Y-%m")]
    with ThreadPoolExecutor(max_workers=6) as pool:
        files = [f for f in pool.map(fetch, jobs) if f]
        # Monthly archives can miss whole days; fill hours that one series has and the other lacks from daily files.
        fills = []
        for contract in CONTRACTS:
            stamps = {kind: {r["open_time"] for f in files if (f["contract"], f["kind"]) == (contract, kind) for r in f["rows"]}
                      for kind in ("klines", "markPriceKlines")}
            for kind, other in (("klines", "markPriceKlines"), ("markPriceKlines", "klines")):
                days = {datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m-%d") for t in stamps[other] - stamps[kind]
                        if t < delivery_ms(contract)}
                fills += [(kind, contract, d) for d in sorted(days)]
        files += [f for f in pool.map(fetch, fills) if f]
    manifest = dict(source="data.binance.vision USDT-M monthly archives", files=[], contracts={})
    for contract in CONTRACTS:
        for kind in ("klines", "markPriceKlines"):
            rows = sorted({r["open_time"]: r for f in files if (f["contract"], f["kind"]) == (contract, kind)
                           for r in f["rows"]}.values(), key=lambda r: r["open_time"])
            path = ROOT / contract / f"{kind}.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            stamps = [r["open_time"] for r in rows]
            gaps = sum(b - a != 3600000 for a, b in zip(stamps, stamps[1:]))
            manifest["contracts"].setdefault(contract, dict(delivery_ms=delivery_ms(contract)))[kind] = dict(
                hours=len(rows), first=stamps[0] if stamps else None, last=stamps[-1] if stamps else None, gaps=gaps,
                sha256=sha256(path.read_bytes()).hexdigest())
    manifest["files"] = [{k: v for k, v in f.items() if k != "rows"} for f in files]
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    for contract, info in manifest["contracts"].items():
        k = info["klines"]
        print(contract, "hours", k["hours"], "gaps", k["gaps"], "marks", info["markPriceKlines"]["hours"],
              datetime.fromtimestamp(k["first"] / 1000, timezone.utc).date() if k["first"] else None)


if __name__ == "__main__":
    main()
