"""Bounded confirmation time, with invalidation and first-cross deduplication."""
from app.data.models import Candle
from app.strategies.pa_smc import DirectionalSweepStrategy


class DirectionalSweepWindowStrategy(DirectionalSweepStrategy):
    name = "perpetual_pa_smc_sweep_confirm_within_3h"

    def entry_conditions(self, candles: list[Candle], fast: float, slow: float) -> tuple[bool, bool]:
        current = candles[-1]
        strong_long = current.close > current.open and current.close >= current.low + (current.high-current.low)*2/3
        strong_short = current.close < current.open and current.close <= current.low + (current.high-current.low)/3
        for offset in range(1, 4):
            index = len(candles)-1-offset
            if index < 20:
                continue
            sweep = candles[index]
            prior = candles[index-20:index]
            waiting = candles[index+1:-1]
            long_entry = (fast > slow and strong_long
                and sweep.low < min(c.low for c in prior) and sweep.close > min(c.low for c in prior)
                and current.close > sweep.high
                and all(c.low >= sweep.low and c.close <= sweep.high for c in waiting))
            short_entry = (fast < slow and strong_short
                and sweep.high > max(c.high for c in prior) and sweep.close < max(c.high for c in prior)
                and current.close < sweep.low
                and all(c.high <= sweep.high and c.close >= sweep.low for c in waiting))
            if long_entry or short_entry:
                return long_entry, short_entry
        return False, False
