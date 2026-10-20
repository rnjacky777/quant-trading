from pathlib import Path
from contextlib import closing
import sqlite3

from app.data.models import Candle, SYMBOLS, TIMEFRAMES_MS


class CandleRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("""
            CREATE TABLE IF NOT EXISTS candles (
                exchange TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp_ms INTEGER NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                PRIMARY KEY (exchange, symbol, timeframe, timestamp_ms)
            )
        """)
        return connection

    def upsert(self, candles: list[Candle]) -> int:
        if not candles:
            return 0
        with closing(self._connect()) as connection:
            with connection:
                connection.executemany("""
                    INSERT INTO candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(exchange, symbol, timeframe, timestamp_ms)
                    DO UPDATE SET open=excluded.open, high=excluded.high,
                                  low=excluded.low, close=excluded.close,
                                  volume=excluded.volume
                """, [tuple(vars(c).values()) for c in candles])
        return len(candles)

    def list_candles(
        self, exchange: str, symbol: str, timeframe: str, limit: int = 100
    ) -> list[Candle]:
        if symbol not in SYMBOLS or timeframe not in TIMEFRAMES_MS or not 1 <= limit <= 1000:
            raise ValueError("invalid candle query")
        with closing(self._connect()) as connection:
            rows = connection.execute("""
                SELECT * FROM candles
                WHERE exchange=? AND symbol=? AND timeframe=?
                ORDER BY timestamp_ms DESC LIMIT ?
            """, (exchange, symbol, timeframe, limit)).fetchall()
        return [Candle(**dict(row)) for row in reversed(rows)]

    def list_range(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        since_ms: int,
        until_ms: int,
    ) -> list[Candle]:
        if symbol not in SYMBOLS or timeframe not in TIMEFRAMES_MS:
            raise ValueError("invalid candle query")
        if since_ms < 0 or until_ms <= since_ms:
            raise ValueError("invalid candle range")
        with closing(self._connect()) as connection:
            rows = connection.execute("""
                SELECT * FROM candles
                WHERE exchange=? AND symbol=? AND timeframe=?
                  AND timestamp_ms>=? AND timestamp_ms<?
                ORDER BY timestamp_ms ASC
            """, (exchange, symbol, timeframe, since_ms, until_ms)).fetchall()
        return [Candle(**dict(row)) for row in rows]
