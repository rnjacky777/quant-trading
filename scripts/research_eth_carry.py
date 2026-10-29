"""Preregistered ETH funding-carry mechanism-transfer test with the frozen experiment-1 rules."""
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.funding_carry import CarryConfig, run_funding_carry
from app.data.models import Candle, FundingRate, MarkPriceCandle
from scripts.fetch_btc_hourly import parse_archive
from scripts.fetch_btc_spot_2022_2023 import KNOWN_OUTAGES
from scripts.research_funding_carry import COSTS
from scripts.research_perpetual_directions import fingerprint

OUTPUT = Path("data/eth-carry-research.json")
DESIGN = Path("docs/research/2026-10-29-eth-carry-design.md")
BTC_CARRY = Path("data/funding-carry-research.json")
PERP, SPOT = Path("data/eth-perpetual-1h"), Path("data/eth-spot-1h")
SOURCES = ("app/backtest/funding_carry.py", "scripts/research_eth_carry.py", str(DESIGN))


def inputs() -> tuple[list[Candle], list[MarkPriceCandle], list[FundingRate], dict[int, Candle], int]:
    klines = json.loads((PERP / "klines.json").read_text(encoding="utf-8"))
    marks = json.loads((PERP / "markPriceKlines.json").read_text(encoding="utf-8"))
    tape = [Candle("binance-usdm", "ETH/USDT", "1h", int(r["open_time"]), *[float(r[k]) for k in ("open", "high", "low", "close", "volume")])
            for r in klines]
    mark = [MarkPriceCandle("binance-usdm", "ETH/USDT", int(r["open_time"]), *[float(r[k]) for k in ("open", "high", "low", "close")], timeframe="1h")
            for r in marks]
    mark_open = {m.timestamp_ms: m.open for m in mark}
    filled, funding = 0, []
    for f in json.loads((PERP / "funding-api.json").read_text(encoding="utf-8")):
        price = float(f["markPrice"]) if f.get("markPrice") else 0.
        if price <= 0:
            price, filled = mark_open[int(f["fundingTime"]) // 3600000 * 3600000], filled + 1
        funding.append(FundingRate("binance-usdm", "ETH/USDT", int(f["fundingTime"]), float(f["fundingRate"]), price))
    spot = {}
    for path in sorted(SPOT.glob("*.zip")):
        for c in parse_archive(path.read_bytes()):
            spot[c.timestamp_ms] = Candle("binance", "ETH/USDT", "1h", c.timestamp_ms, c.open, c.high, c.low, c.close, c.volume)
    return tape, mark, funding, spot, filled


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    tape, marks, funding, spot, filled = inputs()
    btc = {(r["year"], r["cost_case"]): r for r in json.loads(BTC_CARRY.read_text(encoding="utf-8"))["rows"]}
    artifact = dict(schema="eth_carry_transfer_v1", candidate="eth_funding_carry_f067_monthly", design=str(DESIGN),
                    used_for_tuning=False, note="ETH data unused before; correlated with BTC, not fully independent",
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
                    funding_mark_fills=filled, known_spot_outages=sorted(KNOWN_OUTAGES), rows=[])
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        perp = [c for c in tape if start <= c.timestamp_ms < end]
        pm = [m for m in marks if start <= m.timestamp_ms < end]
        rates = [f for f in funding if start <= f.timestamp_ms < end]
        year_spot = {t: c for t, c in spot.items() if start <= t < end}
        prints = dict(perp=fingerprint([asdict(c) for c in perp]), funding=fingerprint([asdict(f) for f in rates]),
                      spot=fingerprint([asdict(year_spot[t]) for t in sorted(year_spot)]))
        for case, costs in COSTS.items():
            result = run_funding_carry(perp, pm, rates, year_spot, CarryConfig(*costs), frozenset(KNOWN_OUTAGES))
            result.pop("equity_curve")
            ref = btc[(year, case)]["result"]
            artifact["rows"].append(dict(year=year, cost_case=case, input_fingerprints=prints, result=result,
                                         btc_return=ref["metrics"]["total_return"], btc_funding_income=ref["funding_income"]))
            m = result["metrics"]
            print(year, case, f"ETH={m['total_return']:+.3%} dd={m['maximum_drawdown']:.3%} sharpe={m['sharpe_ratio']:.2f} "
                  f"funding={result['funding_income']:.1f} fees={result['fees']:.1f} rebal={len(result['rebalances'])} "
                  f"emerg={result['emergency_rebalances']} basis={result['basis_min']:.2%}..{result['basis_max']:.2%} "
                  f"liq={result['liquidated_at_ms']} | BTC={ref['metrics']['total_return']:+.3%}", flush=True)
    rows = artifact["rows"]
    primary = [r["result"]["metrics"]["total_return"] for r in rows if r["cost_case"] == "primary"]
    checks = dict(no_liquidation=all(r["result"]["liquidated_at_ms"] is None for r in rows),
                  all_positive=all(r["result"]["metrics"]["total_return"] > 0 for r in rows),
                  primary_mean=sum(primary) / 4, threshold=.04537291336829191 / 2)
    artifact["checks"] = checks
    artifact["decision"] = ("mechanism_transfer_supported" if checks["no_liquidation"] and checks["all_positive"]
                            and checks["primary_mean"] >= checks["threshold"] else "mechanism_transfer_not_supported")
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(dict(checks=checks, decision=artifact["decision"]), indent=1))


if __name__ == "__main__":
    main()
