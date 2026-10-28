"""Original sweep entries/exits, initial invalidation at the known sweep extreme."""
from dataclasses import replace

from app.data.models import Candle
from app.strategies.directional_intraday import DirectionalSignal
from app.strategies.pa_smc import DirectionalSweepStrategy


class DirectionalSweepStructuralStopStrategy(DirectionalSweepStrategy):
    name = "perpetual_sweep_initial_stop_at_sweep_extreme"

    def generate(self, candles: list[Candle]) -> DirectionalSignal:
        signal=super().generate(candles)
        if not signal.direction:
            return signal
        sweep=candles[-2]
        stop=sweep.low if signal.direction==1 else sweep.high
        return replace(signal,stop_loss_price=stop)
