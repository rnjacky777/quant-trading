"""Keep the sweep invalidation, 4H context reversal and existing time cap."""
from dataclasses import replace

from app.data.models import Candle
from app.strategies.directional_intraday import DirectionalSignal
from app.strategies.multitimeframe import completed_four_hour_closes
from app.strategies.sweep_structural_stop import DirectionalSweepStructuralStopStrategy


class DirectionalSweepContextExitStrategy(DirectionalSweepStructuralStopStrategy):
    name = "perpetual_sweep_structural_stop_4h_context_exit"

    def generate(self,candles: list[Candle]) -> DirectionalSignal:
        signal=super().generate(candles)
        closes=completed_four_hour_closes(candles)
        if len(closes)!=60:
            return signal
        fast,slow=sum(closes[-20:])/20,sum(closes)/60
        return replace(signal,exit_long=fast<=slow,exit_short=fast>=slow)
