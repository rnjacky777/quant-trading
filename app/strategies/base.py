from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import isfinite
from typing import Protocol

from app.data.models import Candle


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Signal:
    symbol: str
    timestamp: datetime
    action: Action
    strength: float
    strategy_name: str
    stop_loss_price: float | None = None
    stop_loss_fraction: float | None = None

    def __post_init__(self) -> None:
        if self.stop_loss_fraction is not None and (
            not isfinite(self.stop_loss_fraction) or not 0 < self.stop_loss_fraction < 1
        ):
            raise ValueError("signal stop fraction must be in (0, 1)")
        if self.stop_loss_price is not None and (
            not isfinite(self.stop_loss_price) or self.stop_loss_price <= 0
        ):
            raise ValueError("signal stop price must be finite and positive")
        if not 0 <= self.strength <= 1:
            raise ValueError("signal strength must be between 0 and 1")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("signal timestamp must have a timezone")


class Strategy(Protocol):
    name: str

    def generate(self, candles: list[Candle]) -> Signal: ...
