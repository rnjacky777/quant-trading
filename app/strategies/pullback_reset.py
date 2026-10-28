"""First short reclaim per observable higher-timeframe pullback reset."""
from app.data.models import Candle
from app.strategies.directional_pullback import DirectionalPullbackStrategy
from app.strategies.multitimeframe import completed_four_hour_closes


def fast_context(candles: list[Candle]) -> float | None:
    closes = completed_four_hour_closes(candles)
    return sum(closes[-20:])/20 if len(closes) >= 20 else None


class DirectionalPullbackResetStrategy(DirectionalPullbackStrategy):
    name = "perpetual_pullback_first_short_after_4h_mean_reset"

    def entry_conditions(self, candles: list[Candle], fast: float, slow: float) -> tuple[bool, bool]:
        long_entry, short_entry = super().entry_conditions(candles, fast, slow)
        if not short_entry:
            return long_entry, False
        # Reconstruct from supplied completed data; no fill-dependent or mutable latch.
        anchor = None
        for j in range(len(candles)-2, 0, -1):
            level = fast_context(candles[:j+1])
            previous_level = fast_context(candles[:j])
            if level is None or previous_level is None:
                break
            if candles[j].close > level and candles[j-1].close <= previous_level:
                anchor = j
                break
        if anchor is None:
            return long_entry, False
        parent = DirectionalPullbackStrategy()
        for j in range(anchor+1, len(candles)-1):
            if parent.generate(candles[:j+1]).direction == -1:
                return long_entry, False
        return long_entry, True
