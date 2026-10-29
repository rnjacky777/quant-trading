"""Additive overlay of a funding-carry book and the frozen trend baseline on one capital base.

Rules: docs/research/2026-10-29-carry-trend-overlay-design.md. Each component
sizes on its own equity (cross-compounding ignored, disclosed). Trend margin is
counted at 2x; the audit only records feasibility and never changes trades.
"""
from dataclasses import asdict

from app.backtest.metrics import calculate_metrics
from app.backtest.models import EquityPoint

TREND_LEVERAGE = 2


def overlay(carry: dict, trend: dict, initial_cash: float = 10000) -> dict:
    """carry: run_funding_carry(..., record_hourly=True); trend: serialized portfolio research result."""
    carry_curve = dict(carry["equity_curve"])
    trend_curve = {p["timestamp_ms"]: p["equity"] for p in trend["equity_curve"]}
    if sorted(carry_curve) != sorted(trend_curve):
        raise ValueError("carry and trend equity curves must share hourly timestamps")
    gross = {p["timestamp_ms"]: p["gross_exposure"] for p in trend["portfolio_curve"]}
    curve = [EquityPoint(t, carry_curve[t] + trend_curve[t] - initial_cash, True) for t in sorted(carry_curve)]
    equity_at = {p.timestamp_ms: p.equity for p in curve}
    collateral_breaches, wallet_breaches = [], []
    worst_wallet_fraction = float("inf")
    max_collateral_fraction = 0.0
    for row in carry["hourly"]:
        t = row["timestamp_ms"]
        trend_gross = gross.get(t, 0.0)
        used = row["spot_value"] + row["short_notional"] / 2 + trend_gross / TREND_LEVERAGE
        max_collateral_fraction = max(max_collateral_fraction, used / equity_at[t])
        if used > equity_at[t] + 1e-6:
            collateral_breaches.append(t)
        wallet = row["perp_equity"] + trend_curve[t] - initial_cash
        notional = row["short_notional"] + trend_gross
        if notional > 0:
            worst_wallet_fraction = min(worst_wallet_fraction, wallet / notional)
        if wallet < 0:
            wallet_breaches.append(t)
    metrics = calculate_metrics(curve, [], initial_cash, "1h", 0.0)
    return dict(metrics=asdict(metrics), final_equity=curve[-1].equity,
                carry_return=carry["metrics"]["total_return"], trend_return=trend["metrics"]["total_return"],
                collateral_breach_hours=len(collateral_breaches), wallet_breach_hours=len(wallet_breaches),
                maximum_collateral_fraction=max_collateral_fraction,
                minimum_wallet_to_notional=worst_wallet_fraction if worst_wallet_fraction != float("inf") else None,
                equity_curve=[(p.timestamp_ms, p.equity) for p in curve])
