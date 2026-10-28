from math import ceil, isfinite


def minimum_required_leverage(*, notional: float, equity: float, maximum: int = 2) -> int:
    """Minimum integer leverage needed for a notional, not permission to trade.

    Futures funding, mark prices and margin validation are separate requirements.
    Changing this number alone does not change the position's absolute PnL.
    """
    if not isfinite(notional) or not isfinite(equity) or notional < 0 or equity <= 0:
        raise ValueError("invalid leverage planning inputs")
    if type(maximum) is not int or maximum < 1:
        raise ValueError("invalid maximum leverage")
    if notional == 0:
        return 0
    required = max(1, ceil(notional/equity))
    if required > maximum:
        raise ValueError("required leverage exceeds the research limit")
    return required


def size_long_position(
    *, equity: float, entry_price: float, stop_price: float,
    risk_fraction: float, max_exposure_fraction: float,
    available_cash: float, fee_bps: float, slippage_bps: float,
) -> float:
    """Unlevered quantity bounded by planned stop loss, exposure and cash.

    Includes entry/exit fees and modeled adverse exit slippage. Gaps through
    the stop can still exceed this budget; a stop is not a guaranteed fill.
    """
    values = (equity, entry_price, stop_price, risk_fraction, max_exposure_fraction,
              available_cash, fee_bps, slippage_bps)
    if not all(isfinite(value) for value in values):
        raise ValueError("sizing inputs must be finite")
    if equity < 0 or available_cash < 0 or entry_price <= 0 or stop_price <= 0:
        raise ValueError("invalid equity, cash or prices")
    if not 0 < risk_fraction <= 1 or not 0 < max_exposure_fraction <= 1:
        raise ValueError("risk and exposure fractions must be in (0, 1]")
    if not 0 <= fee_bps < 10_000 or not 0 <= slippage_bps < 10_000:
        raise ValueError("invalid execution costs")
    if stop_price >= entry_price or equity == 0 or available_cash == 0:
        return 0.0
    fee_rate = fee_bps / 10_000
    exit_price = stop_price * (1 - slippage_bps / 10_000)
    loss_per_unit = entry_price - exit_price + fee_rate * (entry_price + exit_price)
    return min(
        equity * risk_fraction / loss_per_unit,
        equity * max_exposure_fraction / entry_price,
        available_cash / (entry_price * (1 + fee_rate)),
    )
