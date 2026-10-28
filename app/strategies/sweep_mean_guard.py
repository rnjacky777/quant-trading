"""Avoid extending short sweep entries below the completed 4H fast mean."""
from app.data.models import Candle
from app.strategies.pa_smc import DirectionalSweepStrategy


class DirectionalSweepMeanGuardStrategy(DirectionalSweepStrategy):
    name = "perpetual_sweep_short_at_or_above_4h_sma20"

    def entry_conditions(self, candles: list[Candle], fast: float, slow: float) -> tuple[bool, bool]:
        long_entry, short_entry = super().entry_conditions(candles, fast, slow)
        return long_entry, short_entry and candles[-1].close >= fast
