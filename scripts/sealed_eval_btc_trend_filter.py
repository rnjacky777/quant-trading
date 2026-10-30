"""Sealed evaluation 1: BTC spot 50-day filter on 2020-02..2021-09 (registration: 2026-10-30-btc-trend-filter-sealed-registration.md).

Runs once; refuses to overwrite its output. Sealed archives are checked against manifest.json before use.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest import trend_filter
from app.backtest.trend_filter import DAY_MS, FilterConfig, run_trend_filter
from scripts.fetch_btc_hourly import parse_archive
from scripts.fetch_multi_coin_carry import get, ms
from scripts.research_btc_trend_filter import COSTS

SEALED = Path("data/sealed-btc-2020-2021")
OUTPUT = Path("data/sealed-eval-1-btc-trend-filter.json")
REGISTRATION = Path("docs/research/2026-10-30-btc-trend-filter-sealed-registration.md")
PERIODS = (("2020-02-01", "2021-01-01"), ("2021-01-01", "2021-10-01"))
CRASHES = (("2020-03-08", "2020-03-17"), ("2021-05-10", "2021-05-24"))
SOURCES = ("app/backtest/trend_filter.py", "scripts/sealed_eval_btc_trend_filter.py", str(REGISTRATION))


def utc(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def sealed_daily() -> dict[int, tuple[float, float, float, float]]:
    manifest = json.loads((SEALED / "manifest.json").read_text(encoding="utf-8"))
    hours = {}
    for entry in (f for f in manifest["files"] if f["kind"] == "spot_klines"):
        path = SEALED / "spot_klines" / f"{entry['when']}.zip"
        payload = path.read_bytes()
        if sha256(payload).hexdigest() != entry["sha256"]:
            raise ValueError(f"sealed archive changed: {path}")
        for c in parse_archive(payload):
            hours[c.timestamp_ms] = c
    days: dict[int, list] = {}
    for t in sorted(hours):
        days.setdefault(t // DAY_MS * DAY_MS, []).append(hours[t])
    return {d: (bars[0].open, max(b.high for b in bars), min(b.low for b in bars), bars[-1].close) for d, bars in days.items()}


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("sealed evaluation already ran; it is never repeated")
    daily = sealed_daily()
    for r in get("spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2019-12.zip") or []:
        daily[ms(r[0])] = tuple(float(x) for x in r[1:5])
    span = range(utc("2019-12-01"), utc("2021-10-01"), DAY_MS)
    missing = [t for t in span if t not in daily]
    if missing:
        raise SystemExit(f"registered rule: a day without any hourly data fails the evaluation ({len(missing)} days)")
    rows, checks = [], []
    for first, stop in PERIODS:
        start, end = utc(first), utc(stop)
        bars = {t: v for t, v in daily.items() if t < end}
        prices = [daily[t] for t in range(start, end, DAY_MS)]
        peak = dd = 0.0
        for b in prices:
            peak = max(peak, b[3])
            dd = min(dd, b[3] / peak - 1)
        hold = dict(return_=prices[-1][3] / prices[0][0] - 1, max_drawdown=dd)
        curve = {}
        original = trend_filter.calculate_metrics

        def capture(points, *rest, **kw):
            curve.update({p.timestamp_ms: p.equity for p in points})
            return original(points, *rest, **kw)
        trend_filter.calculate_metrics = capture
        try:
            primary = run_trend_filter(bars, FilterConfig(50, *COSTS["primary"]), start, end)
        finally:
            trend_filter.calculate_metrics = original
        results = {case: primary if case == "primary" else run_trend_filter(bars, FilterConfig(50, fee, slip), start, end)
                   for case, (fee, slip) in COSTS.items()}
        crash = {}
        for a, b in CRASHES:
            if start <= utc(a) < end:
                crash[a] = dict(btc=daily[utc(b) - DAY_MS][3] / daily[utc(a)][0] - 1,
                                strategy=curve[utc(b) - DAY_MS] / curve[utc(a) - DAY_MS] - 1)
        period = dict(period=f"{first}..{stop}", btc_hold=hold, crash_windows=crash,
                      results={c: {k: v for k, v in r.items()} for c, r in results.items()})
        m = {c: r["metrics"] for c, r in results.items()}
        period["checks"] = dict(
            drawdown_below_hold=abs(m["primary"]["maximum_drawdown"]) < abs(dd),
            risk_bounds=all(x["maximum_drawdown"] >= -.40 and x["total_return"] >= -.40 for x in m.values()),
            primary_positive=m["primary"]["total_return"] > 0, doubled_positive=m["doubled"]["total_return"] > 0)
        rows.append(period)
        checks.append(all(period["checks"].values()))
        print(period["period"], "hold", f"{hold['return_']:+.1%} dd {dd:.1%}", "|",
              " ".join(f"{c}:{x['total_return']:+.1%}/dd{x['maximum_drawdown']:.1%}" for c, x in m.items()),
              "| trades", results["primary"]["trades"], "invested", results["primary"]["invested_days"], period["checks"], crash)
    artifact = dict(schema="sealed_eval_v1", evaluation=1, registration=str(REGISTRATION), candidate="btc_spot_sma50_filter",
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
                    sealed_manifest_sha256=sha256((SEALED / "manifest.json").read_bytes()).hexdigest(),
                    periods=rows, passed=all(checks))
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print("PASSED" if artifact["passed"] else "FAILED")


if __name__ == "__main__":
    main()
