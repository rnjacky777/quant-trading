"""One original signal, original future exit signals, no subsequent entries."""
from dataclasses import replace

from app.data.models import Candle
from app.strategies.base import Action
from app.strategies.directional_intraday import DirectionalSignal


class FrozenEntryStrategy:
    name = "isolated_original_signal_diagnostic"

    def __init__(self, entry_timestamp_ms: int, signals: dict[int,DirectionalSignal]) -> None:
        self.entry_timestamp_ms=entry_timestamp_ms
        self.signals=signals

    def generate(self, candles: list[Candle]) -> DirectionalSignal:
        if not candles or candles[-1].timestamp_ms not in self.signals:
            raise ValueError("matching precomputed completed-history signal required")
        signal=self.signals[candles[-1].timestamp_ms]
        if candles[-1].timestamp_ms+3600000==self.entry_timestamp_ms:
            return signal
        return replace(signal,action=Action.HOLD,strength=0,direction=0,stop_loss_price=None)
