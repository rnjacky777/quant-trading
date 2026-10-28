from dataclasses import replace
from math import isfinite

from app.data.models import Candle
from app.strategies.base import Action, Signal, Strategy


class FixedPercentageProtection:
    """Attach a fixed percentage invalidation rule to a strategy signal.

    Execution resolves the percentage against the entry fill, preserving the
    existing baseline. ATR/support rules can later supply an absolute stop.
    """

    def __init__(self, strategy: Strategy, stop_loss_pct: float) -> None:
        if not isfinite(stop_loss_pct) or not 0 < stop_loss_pct < 1:
            raise ValueError("stop_loss_pct must be in (0, 1)")
        self.strategy = strategy
        self.stop_loss_pct = stop_loss_pct
        self.name = strategy.name

    def generate(self, candles: list[Candle]) -> Signal:
        signal = self.strategy.generate(candles)
        if signal.action is Action.BUY:
            return replace(signal, stop_loss_fraction=self.stop_loss_pct)
        return signal
