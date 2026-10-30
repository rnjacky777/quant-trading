"""Point-in-time multi-coin carry data (design: docs/research/2026-10-30-multi-coin-carry-design.md).

Phase `rank`: daily perp and spot klines for every archived USDT perpetual with a matching spot pair
(delisted symbols included), then the monthly top-20 universe by previous-month perp quote volume.
Phase `hourly`: 1h perp, mark and spot klines plus funding, only for (symbol, month) pairs in the universe.
Checksums are verified; prints counts only, never returns.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen
from zipfile import ZipFile

from scripts.fetch_btc_hourly import request_bytes

ROOT = Path("data/multi-coin-carry")
BASE = "https://data.binance.vision/data"
RANK_MONTHS = [f"{y}-{m:02d}" for y in range(2021, 2026) for m in range(1, 13) if "2021-12" <= f"{y}-{m:02d}" <= "2025-11"]
TRADE_MONTHS = [f"{y}-{m:02d}" for y in range(2022, 2026) for m in range(1, 13)]
TOP = 20
DAY_MS = 86400000


def listing(prefix: str, tag: str = "Prefix") -> list[str]:
    """Child directories (tag Prefix) or file keys (tag Key) under an archive prefix."""
    out, marker = [], ""
    while True:
        body = request_bytes(f"https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix={quote(prefix)}"
                             f"&marker={quote(marker)}").decode()
        got = re.findall(rf"<{tag}>([^<]+)</{tag}>", body)
        if tag == "Prefix":
            got = got[1:]
        out += [p.rstrip("/").split("/")[-1] for p in got]
        if "<IsTruncated>true</IsTruncated>" not in body or not got:
            return out
        marker = got[-1]


def months_available(prefix: str) -> set[str]:
    """YYYY-MM of every monthly zip under a symbol/interval prefix."""
    return {m.group(1) for name in listing(prefix, "Key") if (m := re.search(r"-(\d{4}-\d{2})\.zip$", name))}


def pairs() -> dict[str, tuple[str, int]]:
    """perp symbol -> (spot symbol, perp/spot price factor)."""
    spot = set(listing("data/spot/monthly/klines/"))
    out = {}
    for perp in sorted(set(listing("data/futures/um/monthly/klines/"))):
        if not perp.endswith("USDT"):
            continue
        if perp in spot:
            out[perp] = (perp, 1)
        elif perp.startswith("1000") and perp[4:] in spot:
            out[perp] = (perp[4:], 1000)
    return out


def ms(value: str) -> int:
    t = int(value)
    return t // 1000 if t >= 10 ** 14 else t


def get(path: str) -> list[list[str]] | None:
    """Download one archive (cached), verify its checksum, return data rows; None when the archive does not exist."""
    target = ROOT / "raw" / path.replace("/", "__")
    if target.exists():
        payload = target.read_bytes()
    else:
        try:
            payload = urlopen(f"{BASE}/{quote(path)}", timeout=30).read()
        except HTTPError as exc:
            if exc.code == 404:
                return None
            payload = request_bytes(f"{BASE}/{quote(path)}")
        expected = request_bytes(f"{BASE}/{quote(path)}.CHECKSUM").decode().split()[0]
        if sha256(payload).hexdigest() != expected:
            raise ValueError("checksum mismatch: " + path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    with ZipFile(BytesIO(payload)) as archive:
        lines = archive.read(archive.namelist()[0]).decode().splitlines()
    return [line.split(",") for line in lines if line[:1].isdigit()]


def rank() -> None:
    symbols = pairs()

    def available(perp: str) -> tuple[str, set[str], set[str]]:
        spot = symbols[perp][0]
        return (perp, months_available(f"data/futures/um/monthly/klines/{perp}/1d/"),
                months_available(f"data/spot/monthly/klines/{spot}/1d/"))
    with ThreadPoolExecutor(max_workers=16) as pool:
        both = {p: a & b for p, a, b in pool.map(available, symbols)}
    jobs = [(p, m) for p in symbols for m in RANK_MONTHS if m in both[p]]

    def daily(job: tuple[str, str]) -> tuple[str, str, dict, set]:
        perp, month = job
        spot = symbols[perp][0]
        rows = get(f"futures/um/monthly/klines/{perp}/1d/{perp}-1d-{month}.zip") or []
        spot_rows = get(f"spot/monthly/klines/{spot}/1d/{spot}-1d-{month}.zip") or []
        return perp, month, {ms(r[0]): float(r[7]) for r in rows}, {ms(r[0]) for r in spot_rows}
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(daily, jobs))
    volume: dict[str, dict[int, float]] = {}
    spot_days: dict[str, set[int]] = {}
    for perp, _, v, s in results:
        volume.setdefault(perp, {}).update(v)
        spot_days.setdefault(perp, set()).update(s)
    universe = {}
    for month in TRADE_MONTHS:
        start = int(datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc).timestamp() * 1000)
        window = range(start - 30 * DAY_MS, start, DAY_MS)
        eligible = {p: sum(volume[p][d] for d in window) for p in symbols
                    if all(d in volume.get(p, {}) and d in spot_days.get(p, set()) for d in window)}
        universe[month] = sorted(eligible, key=lambda p: (-eligible[p], p))[:TOP]
    out = dict(pairs={p: list(v) for p, v in symbols.items()}, universe=universe,
               rule=f"top {TOP} by previous 30 complete UTC days perp quote volume; every day needs perp and spot daily data")
    (ROOT / "universe.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("pairs", len(symbols), "distinct universe members", len({p for u in universe.values() for p in u}))


def hourly() -> None:
    meta = json.loads((ROOT / "universe.json").read_text(encoding="utf-8"))
    need = sorted({(p, m) for m, members in meta["universe"].items() for p in members})
    # Selection needs the previous month's funding as well.
    funding_need = sorted({(p, prev) for p, m in need for prev in (m, previous(m))})

    def bars(job: tuple[str, str]) -> tuple[str, str, dict]:
        perp, month = job
        spot = meta["pairs"][perp][0]
        rows = dict(
            perp=get(f"futures/um/monthly/klines/{perp}/1h/{perp}-1h-{month}.zip"),
            marks=get(f"futures/um/monthly/markPriceKlines/{perp}/1h/{perp}-1h-{month}.zip"),
            spot=get(f"spot/monthly/klines/{spot}/1h/{spot}-1h-{month}.zip"))
        return perp, month, {k: [[ms(r[0]), *map(float, r[1:5])] for r in v or []] for k, v in rows.items()}

    def funding(job: tuple[str, str]) -> tuple[str, str, list]:
        perp, month = job
        rows = get(f"futures/um/monthly/fundingRate/{perp}/{perp}-fundingRate-{month}.zip") or []
        return perp, month, [[int(r[0]), float(r[2])] for r in rows]
    with ThreadPoolExecutor(max_workers=16) as pool:
        hourly_rows = list(pool.map(bars, need))
        funding_rows = list(pool.map(funding, funding_need))
    store: dict[str, dict] = {}
    for perp, month, data in hourly_rows:
        for kind, rows in data.items():
            store.setdefault(perp, {}).setdefault(kind, {}).update({r[0]: r[1:] for r in rows})
    # Monthly archives can miss whole days; refill those days from daily archives.
    paths = dict(perp="futures/um/daily/klines/{p}/1h/{p}-1h-{d}.zip",
                 marks="futures/um/daily/markPriceKlines/{p}/1h/{p}-1h-{d}.zip",
                 spot="spot/daily/klines/{s}/1h/{s}-1h-{d}.zip")
    fills = []
    for perp, month in need:
        start = int(datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc).timestamp() * 1000)
        y, m = map(int, month.split("-"))
        end = int(datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        for kind in paths:
            have = store.get(perp, {}).get(kind, {})
            days = sorted({datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m-%d")
                           for t in range(start, end, 3600000) if t not in have})
            fills += [(perp, kind, d) for d in days]

    def daily(job: tuple[str, str, str]) -> tuple[str, str, list]:
        perp, kind, day = job
        rows = get(paths[kind].format(p=perp, s=meta["pairs"][perp][0], d=day)) or []
        return perp, kind, [[ms(r[0]), *map(float, r[1:5])] for r in rows]
    with ThreadPoolExecutor(max_workers=16) as pool:
        for perp, kind, rows in pool.map(daily, fills):
            store.setdefault(perp, {}).setdefault(kind, {}).update({r[0]: r[1:] for r in rows})
    print("daily fill requests", len(fills))
    for perp, month, rows in funding_rows:
        store.setdefault(perp, {}).setdefault("funding", {}).update({r[0]: r[1] for r in rows})
    for perp, data in store.items():
        (ROOT / "hourly").mkdir(parents=True, exist_ok=True)
        (ROOT / "hourly" / f"{perp}.json").write_text(json.dumps({k: sorted(v.items()) for k, v in data.items()}), encoding="utf-8")
    empty = [(p, m) for p, m, d in hourly_rows if not all(d.values())]
    print("symbols", len(store), "symbol-months", len(need), "symbol-months with an empty series", len(empty))


def previous(month: str) -> str:
    y, m = map(int, month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


if __name__ == "__main__":
    {"rank": rank, "hourly": hourly}[sys.argv[1]]()
