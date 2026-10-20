from datetime import datetime, timezone

from app.data.models import Candle
from app.strategies.base import Action, Signal


class BuyAndHoldStrategy:
    name = "buy_and_hold"

    def generate(self, candles: list[Candle]) -> Signal:
        if not candles:
            raise ValueError("strategy needs candle history")
        candle = candles[-1]
        return Signal(
            symbol=candle.symbol,
            timestamp=datetime.fromtimestamp(candle.timestamp_ms / 1000, timezone.utc),
            action=Action.BUY,
            strength=1.0,
            strategy_name=self.name,
        )
