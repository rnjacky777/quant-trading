from datetime import datetime, timezone

from app.data.models import Candle
from app.strategies.base import Action, Signal


class MovingAverageTrendStrategy:
    def __init__(self, fast_period: int = 20, slow_period: int = 60) -> None:
        if fast_period < 1 or slow_period <= fast_period:
            raise ValueError("periods must satisfy 1 <= fast < slow")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.name = f"sma_{fast_period}_{slow_period}_trend"

    def generate(self, candles: list[Candle]) -> Signal:
        if not candles:
            raise ValueError("strategy needs candle history")
        candle = candles[-1]
        action = Action.HOLD
        strength = 0.0
        if len(candles) >= self.slow_period:
            closes = [item.close for item in candles]
            fast = sum(closes[-self.fast_period:]) / self.fast_period
            slow = sum(closes[-self.slow_period:]) / self.slow_period
            if fast > slow:
                action = Action.BUY
            elif fast < slow:
                action = Action.SELL
            strength = min(abs(fast / slow - 1), 1.0)
        return Signal(
            symbol=candle.symbol,
            timestamp=datetime.fromtimestamp(candle.timestamp_ms / 1000, timezone.utc),
            action=action,
            strength=strength,
            strategy_name=self.name,
        )
