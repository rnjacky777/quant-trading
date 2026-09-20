from time import time

from app.data.models import Candle, SYMBOLS, TIMEFRAMES_MS
from app.exchange.base import HistoricalDataProvider


def download_candles(
    provider: HistoricalDataProvider,
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int,
    *,
    page_size: int = 500,
    max_pages: int = 1000,
    now_ms: int | None = None,
) -> list[Candle]:
    """Fetch closed candles in [since_ms, until_ms); reject stalled pagination."""
    if symbol not in SYMBOLS or timeframe not in TIMEFRAMES_MS:
        raise ValueError("unsupported symbol or timeframe")
    if since_ms < 0 or until_ms <= since_ms or page_size < 1 or max_pages < 1:
        raise ValueError("invalid download bounds")
    interval = TIMEFRAMES_MS[timeframe]
    clock_ms = int(time() * 1000) if now_ms is None else now_ms
    end_ms = min(until_ms, clock_ms - interval + 1)
    cursor = since_ms
    result: dict[int, Candle] = {}
    for _ in range(max_pages):
        if cursor >= end_ms:
            return [result[k] for k in sorted(result)]
        raw = provider.fetch_ohlcv(symbol, timeframe, cursor, page_size)
        if not raw:
            return [result[k] for k in sorted(result)]
        previous = -1
        for row in raw:
            if len(row) != 6:
                raise ValueError("OHLCV row must have six values")
            timestamp = int(row[0])
            if timestamp <= previous:
                raise ValueError("provider returned out-of-order candles")
            previous = timestamp
            if since_ms <= timestamp < end_ms and timestamp >= cursor:
                result[timestamp] = Candle(
                    provider.exchange_id, symbol, timeframe, timestamp,
                    *map(float, row[1:]),
                )
        if previous < cursor:
            raise ValueError("provider pagination did not advance")
        cursor = previous + interval
    if cursor < end_ms:
        raise RuntimeError("max_pages reached before end of requested range")
    return [result[k] for k in sorted(result)]
