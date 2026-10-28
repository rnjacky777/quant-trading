from datetime import datetime, timezone
from math import isfinite

from app.data.models import Candle
from app.strategies.base import Action, Signal


class MeanReversionStrategy:
    """Buy below a trailing mean; exit at the mean; hold between thresholds."""

    def __init__(self, lookback: int = 20, entry_deviation: float = 0.05) -> None:
        if type(lookback) is not int or lookback < 2:
            raise ValueError("lookback must be an integer >= 2")
        if not isfinite(entry_deviation) or not 0 < entry_deviation < 1:
            raise ValueError("entry_deviation must be in (0, 1)")
        self.lookback = lookback
        self.entry_deviation = float(entry_deviation)
        self.name = f"mean_reversion_{lookback}_{self.entry_deviation!r}"

    def generate(self, candles: list[Candle]) -> Signal:
        if not candles:
            raise ValueError("strategy needs candle history")
        candle = candles[-1]
        action, strength = Action.HOLD, 0.0
        if len(candles) >= self.lookback:
            mean = sum(item.close for item in candles[-self.lookback:]) / self.lookback
            deviation = candle.close / mean - 1
            if candle.close <= mean * (1 - self.entry_deviation):
                action = Action.BUY
            elif candle.close >= mean:
                action = Action.SELL
            strength = min(abs(deviation), 1.0)
        return Signal(
            candle.symbol,
            datetime.fromtimestamp(candle.timestamp_ms / 1000, timezone.utc),
            action, strength, self.name,
        )
