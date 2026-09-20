from dataclasses import dataclass
from math import isfinite

SYMBOLS = frozenset({"BTC/USDT", "ETH/USDT"})
TIMEFRAMES_MS = {"4h": 4 * 60 * 60 * 1000, "1d": 24 * 60 * 60 * 1000}


@dataclass(frozen=True)
class Candle:
    exchange: str
    symbol: str
    timeframe: str
    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.symbol not in SYMBOLS or self.timeframe not in TIMEFRAMES_MS:
            raise ValueError("unsupported symbol or timeframe")
        if not self.exchange or self.timestamp_ms < 0:
            raise ValueError("invalid exchange or timestamp")
        prices = (self.open, self.high, self.low, self.close)
        if not all(isfinite(x) and x > 0 for x in prices):
            raise ValueError("prices must be finite and positive")
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError("inconsistent OHLC prices")
        if self.high < self.low or not isfinite(self.volume) or self.volume < 0:
            raise ValueError("invalid high, low, or volume")
