"""Delay a swing breakout until one further completed 4H bar confirms it."""
from app.data.models import Candle
from app.strategies.directional_swing import DirectionalSwingStrategy


class DirectionalSwingConfirmationStrategy(DirectionalSwingStrategy):
    name = "perpetual_swing_next_4h_confirmation"

    def entry_conditions(self, bars: list[Candle], fast: float, slow: float) -> tuple[bool, bool]:
        if len(bars) < 61:
            return False, False
        breakout, confirmation = bars[-2], bars[-1]
        reference = bars[-22:-2]
        previous_fast = sum(c.close for c in bars[-21:-1]) / 20
        previous_slow = sum(c.close for c in bars[-61:-1]) / 60
        previous_ranges = [max(bars[i].high - bars[i].low,
                               abs(bars[i].high - bars[i - 1].close),
                               abs(bars[i].low - bars[i - 1].close))
                           for i in range(len(bars) - 15, len(bars) - 1)]
        # The preceding completed bar must itself have qualified as a breakout.
        if sum(previous_ranges) / 14 / breakout.close < .006:
            return False, False
        return (
            previous_fast > previous_slow and fast > slow
            and breakout.close > max(c.high for c in reference)
            and confirmation.close > breakout.close,
            previous_fast < previous_slow and fast < slow
            and breakout.close < min(c.low for c in reference)
            and confirmation.close < breakout.close,
        )
