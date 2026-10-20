from math import isfinite


def execution_price(reference_price: float, slippage_bps: float, *, is_buy: bool) -> float:
    if not isfinite(reference_price) or reference_price <= 0:
        raise ValueError("reference price must be finite and positive")
    if not isfinite(slippage_bps) or slippage_bps < 0:
        raise ValueError("slippage must be finite and non-negative")
    direction = 1 if is_buy else -1
    return reference_price * (1 + direction * slippage_bps / 10_000)
