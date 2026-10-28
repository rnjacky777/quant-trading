"""Frozen breakout boundary for the delayed-confirmation swing research rule."""
from app.data.aggregation import completed_four_hour_bars
from app.data.models import Candle


def breakout_boundary(history: list[Candle], direction: int) -> float:
    bars = completed_four_hour_bars(history)
    if direction not in (-1, 1) or len(bars) < 22:
        raise ValueError("completed breakout history and direction required")
    reference = bars[-22:-2]
    return max(c.high for c in reference) if direction == 1 else min(c.low for c in reference)


def breakout_failed(history: list[Candle], direction: int, boundary: float, *, hourly: bool = False) -> bool:
    # Default retains 4h confirmation; hourly research still uses completed closes.
    return bool(history and (hourly or history[-1].timestamp_ms % 14400000 == 10800000)
                and direction * (history[-1].close - boundary) < 0)
