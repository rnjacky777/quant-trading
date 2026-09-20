from typing import Any


class CcxtHistoricalProvider:
    """Read-only public market data adapter. No keys or order methods."""

    def __init__(self, exchange_id: str = "binance") -> None:
        import ccxt

        if not hasattr(ccxt, exchange_id):
            raise ValueError(f"unknown CCXT exchange: {exchange_id}")
        self.exchange_id = exchange_id
        factory: Any = getattr(ccxt, exchange_id)
        self._client = factory({"enableRateLimit": True, "timeout": 10000})
        if not self._client.has.get("fetchOHLCV"):
            raise ValueError(f"{exchange_id} does not support OHLCV")

    def fetch_ohlcv(
        self, symbol: str, timeframe: str, since_ms: int, limit: int
    ) -> list[list[float]]:
        return self._client.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=limit)
