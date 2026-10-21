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


@dataclass(frozen=True)
class CandleCoverage:
    symbol: str
    timeframe: str
    candle_count: int
    first_timestamp_ms: int
    last_timestamp_ms: int


@dataclass(frozen=True)
class FundingRate:
    exchange: str
    symbol: str
    timestamp_ms: int
    rate: float
    mark_price: float

    def __post_init__(self) -> None:
        if self.symbol not in SYMBOLS or not self.exchange or self.timestamp_ms < 0:
            raise ValueError("invalid funding rate identity")
        if not isfinite(self.rate) or not isfinite(self.mark_price) or self.mark_price <= 0:
            raise ValueError("invalid funding rate values")


@dataclass(frozen=True)
class MarkPriceCandle:
    exchange: str
    symbol: str
    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    timeframe: str = "1m"

    def __post_init__(self) -> None:
        if self.symbol not in SYMBOLS or not self.exchange or self.timestamp_ms < 0:
            raise ValueError("invalid mark price identity")
        if self.timeframe not in {"1m", "4h", "1d"}:
            raise ValueError("unsupported mark price timeframe")
        prices = (self.open, self.high, self.low, self.close)
        if not all(isfinite(value) and value > 0 for value in prices):
            raise ValueError("mark prices must be finite and positive")
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError("inconsistent mark price OHLC")
