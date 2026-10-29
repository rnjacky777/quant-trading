"""Preregistered coupled carry (f=0.43, 5% drift rebalance) + frozen trend baseline: 4 years x 4 cost cases."""
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.carry_overlay import overlay
from app.backtest.funding_carry import CarryConfig, run_funding_carry
from scripts.fetch_btc_spot_2022_2023 import KNOWN_OUTAGES
from scripts.research_funding_carry import BASELINE, BASELINE_COST, COSTS, spot_candles
from scripts.research_perpetual_directions import fingerprint
from scripts.research_risk_budget import late_inputs
from scripts.validate_baseline_2022_2023 import load_inputs

OUTPUT = Path("data/carry-trend-coupled-research.json")
DESIGN = Path("docs/research/2026-10-29-carry-trend-coupled-design.md")
CARRY_FRACTION = .43
DRIFT_BAND = .05
SOURCES = ("app/backtest/funding_carry.py", "app/backtest/carry_overlay.py",
           "scripts/research_carry_trend_coupled.py", str(DESIGN), str(BASELINE))


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    early, late, spot = load_inputs(), late_inputs(), spot_candles()
    trend_rows = [r for r in json.loads(BASELINE.read_text(encoding="utf-8"))["rows"]
                  if r["variant"] == "portfolio_swing_failure_exit"]
    artifact = dict(schema="carry_trend_coupled_screen_v1", candidate="carry_f043_drift5_plus_trend_baseline", parent_experiment="carry_f05_plus_trend_baseline",
                    category="new_mechanism_combination", used_for_tuning=True, independent_validation=False,
                    post_hoc_combination=True, informed_by_failure="docs/research/2026-10-29-carry-trend-overlay-results.md", design=str(DESIGN), carry_fraction=CARRY_FRACTION, drift_band=DRIFT_BAND,
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
                    approximations=["components size on own equity; cross-compounding ignored",
                                    "trend PnL from 1x snapshot, margin counted at 2x",
                                    "same-symbol carry short and trend lots need hedge mode or subaccounts (unverified)"],
                    rows=[])
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        tape, marks, funding = early[:3] if year < 2024 else late
        perp = [c for c in tape if start <= c.timestamp_ms < end]
        pm = [m for m in marks if start <= m.timestamp_ms < end]
        rates = [f for f in funding if start <= f.timestamp_ms < end]
        year_spot = {t: c for t, c in spot.items() if start <= t < end}
        for case, (pf, ps, sf, ss) in COSTS.items():
            fee, slip = BASELINE_COST[case]
            trend = next(r for r in trend_rows if r["year"] == year and (r["fee_bps"], r["slippage_bps"]) == (fee, slip))
            carry = run_funding_carry(perp, pm, rates, year_spot, CarryConfig(pf, ps, sf, ss, target_fraction=CARRY_FRACTION, drift_band=DRIFT_BAND),
                                      frozenset(KNOWN_OUTAGES), record_hourly=True)
            if carry["liquidated_at_ms"] is not None:
                raise ValueError(f"{year}/{case}: carry liquidated")
            combined = overlay(carry, trend["result"])
            curve = combined.pop("equity_curve")
            months, previous = {}, 10000.
            for ts, equity in curve:
                months[datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m")] = equity
            artifact["rows"].append(dict(year=year, cost_case=case, trend_input_fingerprints=trend["input_fingerprints"],
                carry_input_fingerprint=fingerprint([asdict(c) for c in perp]), combined=combined,
                carry_metrics=carry["metrics"], carry_emergency_rebalances=carry["emergency_rebalances"], carry_drift_rebalances=sum(r["reason"] == "drift" for r in carry["rebalances"]), carry_fees=carry["fees"] + carry["slippage"],
                trend_metrics=trend["result"]["metrics"], month_end_equity=months))
            m = combined["metrics"]
            print(year, case, f"overlay={m['total_return']:+.3%} dd={m['maximum_drawdown']:.3%} sharpe={m['sharpe_ratio']:.2f} "
                  f"| carry={combined['carry_return']:+.3%} trend={combined['trend_return']:+.3%} "
                  f"| collateral_max={combined['maximum_collateral_fraction']:.2f} breaches={combined['collateral_breach_hours']}/"
                  f"{combined['wallet_breach_hours']} wallet/notional_min={combined['minimum_wallet_to_notional']:.3f}", flush=True)
    rows = artifact["rows"]
    def mean(case: str) -> float:
        return sum(r["combined"]["metrics"]["total_return"] for r in rows if r["cost_case"] == case) / 4
    checks = dict(no_breaches=all(r["combined"]["collateral_breach_hours"] == 0 and r["combined"]["wallet_breach_hours"] == 0 for r in rows),
                  primary_mean=mean("primary"), doubled_mean=mean("doubled"),
                  worst_year=min(r["combined"]["metrics"]["total_return"] for r in rows),
                  worst_drawdown=min(r["combined"]["metrics"]["maximum_drawdown"] for r in rows))
    rest = checks["no_breaches"] and checks["doubled_mean"] > 0 and checks["worst_year"] >= -.03 and checks["worst_drawdown"] >= -.10
    artifact["objective_checks"] = checks
    artifact["decision"] = ("screen_passed" if rest and checks["primary_mean"] >= .05 else
                            "keep_tradeoff_candidate" if rest else "reject")
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(dict(checks=checks, decision=artifact["decision"]), indent=1))


if __name__ == "__main__":
    main()
