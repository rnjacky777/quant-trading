"""A causal rolling-three-bar structure proxy, not a full ICT/SMC replica."""
from app.data.models import Candle
from app.strategies.sweep_structural_stop import DirectionalSweepStructuralStopStrategy


class DirectionalSweepStructureConfirmStrategy(DirectionalSweepStructuralStopStrategy):
    name = "perpetual_sweep_past_3bar_structure_confirmation"

    def entry_conditions(self,candles: list[Candle],fast: float,slow: float) -> tuple[bool,bool]:
        long_entry,short_entry=super().entry_conditions(candles,fast,slow)
        if len(candles)<4:
            return False,False
        structure=candles[-4:-1]
        close=candles[-1].close
        return (long_entry and close>max(c.high for c in structure),
                short_entry and close<min(c.low for c in structure))
