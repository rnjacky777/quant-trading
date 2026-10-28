from datetime import datetime, timezone
from math import isfinite

from app.data.models import Candle
from app.strategies.base import Action, Signal


class MomentumStrategy:
    """Long/cash target based on close-to-close return over lookback bars."""

    def __init__(self, lookback: int = 20, threshold: float = 0.0) -> None:
        if type(lookback) is not int or lookback < 1:
            raise ValueError("lookback must be a positive integer")
        if not isfinite(threshold) or not 0 <= threshold < 1:
            raise ValueError("threshold must be in [0, 1)")
        self.lookback = lookback
        self.threshold = float(threshold)
        self.name = f"momentum_{lookback}_{self.threshold!r}"

    def generate(self, candles: list[Candle]) -> Signal:
        if not candles:
            raise ValueError("strategy needs candle history")
        candle = candles[-1]
        action, strength = Action.HOLD, 0.0
        if len(candles) >= self.lookback + 1:
            change = candle.close / candles[-self.lookback - 1].close - 1
            action = Action.BUY if change > self.threshold else Action.SELL
            strength = min(abs(change), 1.0)
        return Signal(
            candle.symbol,
            datetime.fromtimestamp(candle.timestamp_ms / 1000, timezone.utc),
            action, strength, self.name,
        )
