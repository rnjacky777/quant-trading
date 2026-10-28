"""Gate hourly BUY signals with fully completed, UTC-aligned 4h closes."""
from dataclasses import replace

from app.data.models import Candle
from app.strategies.base import Action, Signal, Strategy


def completed_four_hour_closes(candles: list[Candle], count: int = 60) -> list[float]:
    if not candles or any(c.timeframe != "1h" for c in candles[-243:]):
        raise ValueError("4h trend filter requires hourly input")
    closes = []
    for index in range(len(candles) - 1, 2, -1):
        last = candles[index]
        # Only the fourth completed hourly bar closes a UTC four-hour bucket.
        if last.timestamp_ms % 14400000 != 10800000:
            continue
        group = candles[index-3:index+1]
        if [c.timestamp_ms for c in group] != list(range(last.timestamp_ms-10800000, last.timestamp_ms+1, 3600000)):
            raise ValueError("incomplete four-hour bucket")
        closes.append(last.close)
        if len(closes) == count:
            break
    return list(reversed(closes))


class CompletedFourHourTrend:
    """Signal-only decorator; exits remain unconditional, sizing is elsewhere."""

    def __init__(self, strategy: Strategy) -> None:
        self.strategy = strategy
        self.name = strategy.name

    def generate(self, candles: list[Candle]) -> Signal:
        signal = self.strategy.generate(candles)
        if signal.action is not Action.BUY:
            return signal
        closes = completed_four_hour_closes(candles)
        permitted = len(closes) == 60 and sum(closes[-20:])/20 > sum(closes)/60
        return signal if permitted else replace(signal, action=Action.HOLD, strength=0.0)
