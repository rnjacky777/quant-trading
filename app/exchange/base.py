from typing import Protocol


class HistoricalDataProvider(Protocol):
    exchange_id: str

    def fetch_ohlcv(
        self, symbol: str, timeframe: str, since_ms: int, limit: int
    ) -> list[list[float]]: ...
