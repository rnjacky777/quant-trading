"""Preregistered funding-carry screen: 4 years x 4 cost cases (tuning data, not validation)."""
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.funding_carry import CarryConfig, run_funding_carry
from app.data.models import Candle
from scripts.fetch_btc_hourly import parse_archive
from scripts.fetch_btc_spot_2022_2023 import KNOWN_OUTAGES
from scripts.research_perpetual_directions import fingerprint
from scripts.research_risk_budget import late_inputs
from scripts.validate_baseline_2022_2023 import load_inputs

OUTPUT = Path("data/funding-carry-research.json")
DESIGN = Path("docs/research/2026-10-29-funding-carry-design.md")
BASELINE = Path("data/perpetual-risk-budget-055.json")
# (perp fee, perp slippage, spot fee, spot slippage)
COSTS = {"primary": (5, 5, 10, 5), "10/5": (10, 5, 10, 5), "doubled": (10, 10, 20, 10), "stress": (20, 10, 20, 10)}
BASELINE_COST = {"primary": (5, 5), "10/5": (10, 5), "doubled": (10, 10), "stress": (20, 10)}
SOURCES = ("app/backtest/funding_carry.py", "scripts/research_funding_carry.py", str(DESIGN))


def spot_candles() -> dict[int, Candle]:
    out = {}
    for folder in (Path("data/btc-spot-1h-2022-2023"), Path("data/btc-spot-1h")):
        for path in sorted(folder.glob("*.zip")):
            for c in parse_archive(path.read_bytes()):
                out[c.timestamp_ms] = c
    return out


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    early, late, spot = load_inputs(), late_inputs(), spot_candles()
    baseline_rows = [r for r in json.loads(BASELINE.read_text(encoding="utf-8"))["rows"]
                     if r["variant"] == "portfolio_swing_failure_exit"]
    artifact = dict(schema="funding_carry_screen_v1", candidate="funding_carry_f067_monthly", category="new_mechanism",
                    used_for_tuning=True, independent_validation=False, design=str(DESIGN),
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
                    funding_mark_fills=early[3], known_spot_outages=sorted(KNOWN_OUTAGES),
                    assumptions=["free instant wallet transfers", "flat MMR 2% unverified brackets",
                                 "spot taker 10bps not yet checked against official schedule",
                                 "exchange counterparty risk not modelled"], rows=[])
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        tape, marks, funding = early[:3] if year < 2024 else late
        perp = [c for c in tape if start <= c.timestamp_ms < end]
        pm = [m for m in marks if start <= m.timestamp_ms < end]
        rates = [f for f in funding if start <= f.timestamp_ms < end]
        year_spot = {t: c for t, c in spot.items() if start <= t < end}
        prints = dict(perp=fingerprint([asdict(c) for c in perp]), marks=fingerprint([asdict(m) for m in pm]),
                      funding=fingerprint([asdict(f) for f in rates]),
                      spot=fingerprint([asdict(year_spot[t]) for t in sorted(year_spot)]))
        for case, (pf, ps, sf, ss) in COSTS.items():
            result = run_funding_carry(perp, pm, rates, year_spot, CarryConfig(pf, ps, sf, ss),
                                       frozenset(KNOWN_OUTAGES))
            fee, slip = BASELINE_COST[case]
            base = next(r for r in baseline_rows if r["year"] == year and (r["fee_bps"], r["slippage_bps"]) == (fee, slip))
            curve = result.pop("equity_curve")
            months = {}
            for ts, equity in curve:
                months[datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m")] = equity
            artifact["rows"].append(dict(year=year, cost_case=case, perp_fee_bps=pf, perp_slippage_bps=ps,
                spot_fee_bps=sf, spot_slippage_bps=ss, input_fingerprints=prints, result=result,
                month_end_equity=months, baseline_metrics=base["result"]["metrics"]))
            m = result["metrics"]
            print(year, case, f"return={m['total_return']:+.3%} dd={m['maximum_drawdown']:.3%} "
                  f"sharpe={m['sharpe_ratio']:.2f} funding={result['funding_income']:.1f} fees={result['fees']:.1f} "
                  f"slip={result['slippage']:.1f} rebal={len(result['rebalances'])} emerg={result['emergency_rebalances']} "
                  f"maxlev={result['maximum_perp_leverage']:.2f} liq={result['liquidated_at_ms']} "
                  f"| baseline={base['result']['metrics']['total_return']:+.3%}", flush=True)
    rows = artifact["rows"]
    def mean(case: str) -> float:
        return sum(r["result"]["metrics"]["total_return"] for r in rows if r["cost_case"] == case) / 4
    checks = dict(no_liquidation=all(r["result"]["liquidated_at_ms"] is None for r in rows),
                  primary_mean=mean("primary"), doubled_mean=mean("doubled"),
                  worst_year=min(r["result"]["metrics"]["total_return"] for r in rows),
                  worst_drawdown=min(r["result"]["metrics"]["maximum_drawdown"] for r in rows))
    rest = checks["no_liquidation"] and checks["doubled_mean"] > 0 and checks["worst_year"] >= -.03 and checks["worst_drawdown"] >= -.10
    artifact["objective_checks"] = checks
    artifact["decision"] = ("screen_passed" if rest and checks["primary_mean"] >= .05 else
                            "keep_tradeoff_candidate" if rest else "reject")
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(dict(checks=checks, decision=artifact["decision"]), indent=1))


if __name__ == "__main__":
    main()
