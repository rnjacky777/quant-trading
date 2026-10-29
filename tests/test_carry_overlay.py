import pytest

from app.backtest.carry_overlay import overlay


def carry(equities, spot=5000, short=5000, perp=2500):
    curve = list(enumerate(equities))
    return dict(equity_curve=curve, metrics=dict(total_return=equities[-1] / 10000 - 1),
                hourly=[dict(timestamp_ms=t, spot_value=spot, short_notional=short, perp_equity=perp) for t, _ in curve[1:]])


def trend(equities, gross=0.0):
    return dict(equity_curve=[dict(timestamp_ms=t, equity=e) for t, e in enumerate(equities)],
                portfolio_curve=[dict(timestamp_ms=t, gross_exposure=gross) for t in range(1, len(equities))],
                metrics=dict(total_return=equities[-1] / 10000 - 1))


def test_overlay_adds_component_pnl_on_one_capital_base():
    result = overlay(carry([10000, 10100, 10300]), trend([10000, 9950, 10200]))
    assert [e for _, e in result["equity_curve"]] == [10000, 10050, 10500]
    assert result["metrics"]["total_return"] == pytest.approx(.05)
    assert result["collateral_breach_hours"] == 0 and result["wallet_breach_hours"] == 0


def test_audit_counts_trend_margin_at_two_x_and_flags_breaches():
    ok = overlay(carry([10000] * 3), trend([10000] * 3, gross=5000))
    assert ok["maximum_collateral_fraction"] == pytest.approx((5000 + 2500 + 2500) / 10000)
    assert ok["collateral_breach_hours"] == 0
    over = overlay(carry([10000] * 3), trend([10000] * 3, gross=6000))
    assert over["collateral_breach_hours"] == 2
    losing = overlay(carry([10000] * 3, perp=100), trend([10000, 9800, 9800]))
    assert losing["wallet_breach_hours"] == 2


def test_misaligned_curves_are_rejected():
    with pytest.raises(ValueError):
        overlay(carry([10000] * 3), trend([10000] * 4))
