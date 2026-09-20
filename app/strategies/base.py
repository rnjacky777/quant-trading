from dataclasses import dataclass
from datetime import datetime
from enum import Enum
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

    def __post_init__(self) -> None:
        if not 0 <= self.strength <= 1:
            raise ValueError("signal strength must be between 0 and 1")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("signal timestamp must have a timezone")


class Strategy(Protocol):
    name: str

    def generate(self, candles: list[Candle]) -> Signal: ...
