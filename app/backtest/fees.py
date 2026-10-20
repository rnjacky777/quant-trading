from math import isfinite


def fee_amount(notional: float, fee_bps: float) -> float:
    if not isfinite(notional) or not isfinite(fee_bps) or notional < 0 or fee_bps < 0:
        raise ValueError("notional and fee must be finite and non-negative")
    return notional * fee_bps / 10_000
