"""One fixed entry-only efficiency filter on the delayed-confirmation parent."""
from app.data.models import Candle
from app.strategies.swing_confirmation import DirectionalSwingConfirmationStrategy


def path_efficiency(closes: list[float]) -> float:
    """Absolute net movement / path movement; flat paths have no direction."""
    if len(closes) < 2:
        return 0.
    movement = sum(abs(b - a) for a, b in zip(closes[:-1], closes[1:]))
    return abs(closes[-1] - closes[0]) / movement if movement else 0.


class DirectionalSwingEfficiencyStrategy(DirectionalSwingConfirmationStrategy):
    name = "perpetual_swing_confirmation_er20_ge_03"

    def entry_conditions(self, bars: list[Candle], fast: float, slow: float) -> tuple[bool, bool]:
        long_entry, short_entry = super().entry_conditions(bars, fast, slow)
        if len(bars) < 21 or path_efficiency([c.close for c in bars[-21:]]) < .3:
            return False, False
        return long_entry, short_entry
