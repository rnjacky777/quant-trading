"""One confirmation-volume gate on the existing completed-4h swing signal."""
from app.data.models import Candle
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy


class DirectionalSwingVolumeStrategy(DirectionalSwingEfficiencyStrategy):
    name='perpetual_swing_confirmation_volume_ge_prior20_mean'

    def entry_conditions(self,bars: list[Candle],fast: float,slow: float) -> tuple[bool,bool]:
        long_entry,short_entry=super().entry_conditions(bars,fast,slow)
        if len(bars)<21 or bars[-1].volume<sum(c.volume for c in bars[-21:-1])/20:
            return False,False
        return long_entry,short_entry
