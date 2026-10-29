"""Read-only public Binance USD-M market data for paper observation.

Public endpoints only: no API key, signature, account or order method.
"""
from collections.abc import Callable
from dataclasses import dataclass
import json
import time
from typing import Protocol
from urllib.error import URLError
from urllib.request import urlopen

from app.data.models import Candle, FundingRate

BASE_URL = "https://fapi.binance.com"
SPOT_URL = "https://api.binance.com"
EXCHANGE = "binance-usdm"
SYMBOL = "BTC/USDT"
HOUR_MS = 3600000


class FeedError(RuntimeError):
    pass


@dataclass(frozen=True)
class Quote:
    """exchange_ms is the book time that prices fills; last_ms is the last trade time."""
    bid: float
    ask: float
    last: float
    exchange_ms: int
    received_ms: int
    last_ms: int = 0


@dataclass(frozen=True)
class MarkSnapshot:
    mark: float
    funding_rate: float
    next_funding_ms: int
    exchange_ms: int
    received_ms: int


class PerpetualFeed(Protocol):
    def server_time(self) -> int: ...
    def closed_hourly(self, since_ms: int) -> list[tuple[Candle, int]]: ...
    def quote(self) -> Quote: ...
    def mark(self) -> MarkSnapshot: ...
    def funding(self, start_ms: int, end_ms: int) -> list[FundingRate]: ...
    def spot_quote(self) -> Quote: ...


class BinanceUsdmPublicFeed:
    def __init__(self, *, clock: Callable[[], int] = lambda: int(time.time() * 1000),
                 timeout: float = 10, attempts: int = 3) -> None:
        self.clock, self.timeout, self.attempts = clock, timeout, attempts

    def _get(self, path: str, base: str = BASE_URL):
        error: Exception | None = None
        for attempt in range(self.attempts):
            try:
                with urlopen(base + path, timeout=self.timeout) as response:
                    return json.loads(response.read())
            except (URLError, TimeoutError, OSError, ValueError) as exc:
                error = exc
                time.sleep(min(2 ** attempt, 4))
        raise FeedError(f"{path.split('?')[0]} failed after {self.attempts} attempts: {error}")

    def server_time(self) -> int:
        return int(self._get("/fapi/v1/time")["serverTime"])

    def closed_hourly(self, since_ms: int) -> list[tuple[Candle, int]]:
        """Completed 1h candles from since_ms with their local receipt time."""
        rows = self._get(f"/fapi/v1/klines?symbol=BTCUSDT&interval=1h&startTime={since_ms}&limit=1500")
        received = self.clock()
        server = self.server_time()
        return [(Candle(EXCHANGE, SYMBOL, "1h", int(r[0]), float(r[1]), float(r[2]), float(r[3]),
                        float(r[4]), float(r[5])), received) for r in rows if int(r[6]) < server]

    def quote(self) -> Quote:
        # /ticker/price is a cached snapshot (seconds old); recent trades give the live last price.
        book = self._get("/fapi/v1/ticker/bookTicker?symbol=BTCUSDT")
        trade = self._get("/fapi/v1/trades?symbol=BTCUSDT&limit=1")[-1]
        return Quote(float(book["bidPrice"]), float(book["askPrice"]), float(trade["price"]),
                     int(book["time"]), self.clock(), int(trade["time"]))

    def mark(self) -> MarkSnapshot:
        row = self._get("/fapi/v1/premiumIndex?symbol=BTCUSDT")
        return MarkSnapshot(float(row["markPrice"]), float(row["lastFundingRate"]), int(row["nextFundingTime"]),
                            int(row["time"]), self.clock())

    def funding(self, start_ms: int, end_ms: int) -> list[FundingRate]:
        rows = self._get(f"/fapi/v1/fundingRate?symbol=BTCUSDT&startTime={start_ms}&endTime={end_ms}&limit=1000")
        # Records without markPrice are omitted here and handled as missing by the runner.
        return [FundingRate(EXCHANGE, SYMBOL, int(r["fundingTime"]), float(r["fundingRate"]), float(r["markPrice"]))
                for r in rows if r.get("markPrice") and float(r["markPrice"]) > 0]

    def spot_quote(self) -> Quote:
        """Spot book has no timestamp; freshness uses the latest spot trade time for both fields."""
        book = self._get("/api/v3/ticker/bookTicker?symbol=BTCUSDT", SPOT_URL)
        trade = self._get("/api/v3/trades?symbol=BTCUSDT&limit=1", SPOT_URL)[-1]
        return Quote(float(book["bidPrice"]), float(book["askPrice"]), float(trade["price"]),
                     int(trade["time"]), self.clock(), int(trade["time"]))
