"""One explicit PA/SMC hypothesis, not a complete discretionary SMC system.

Use a rolling past level, a completed sweep/reclaim, then the NEXT completed
bar's reverse-side break. No future pivots, retroactive order blocks or drawings.
"""
from app.data.models import Candle
from app.strategies.directional_intraday import DirectionalIntradayStrategy


class DirectionalSweepStrategy(DirectionalIntradayStrategy):
    name="perpetual_pa_smc_sweep_confirmation"

    def entry_conditions(self,candles: list[Candle],fast: float,slow: float) -> tuple[bool,bool]:
        if len(candles)<22:
            return False,False
        confirmation,sweep=candles[-1],candles[-2]
        past=candles[-22:-2]
        level_low=min(c.low for c in past)
        level_high=max(c.high for c in past)
        bullish=(sweep.low<level_low and sweep.close>level_low
                 and confirmation.close>sweep.high and confirmation.close>confirmation.open
                 and confirmation.close>=confirmation.low+(confirmation.high-confirmation.low)*2/3)
        bearish=(sweep.high>level_high and sweep.close<level_high
                 and confirmation.close<sweep.low and confirmation.close<confirmation.open
                 and confirmation.close<=confirmation.low+(confirmation.high-confirmation.low)/3)
        return fast>slow and bullish,fast<slow and bearish
