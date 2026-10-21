from contextlib import closing
from pathlib import Path
import sqlite3

from app.data.models import FundingRate, MarkPriceCandle, SYMBOLS
from app.risk.margin import MaintenanceMarginModel, MarginBracket


class DerivativesRepository:
    """SQLite storage for reproducible perpetual-futures inputs."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS funding_rates (
                exchange TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timestamp_ms INTEGER NOT NULL,
                rate REAL NOT NULL,
                mark_price REAL NOT NULL,
                PRIMARY KEY (exchange, symbol, timestamp_ms)
            );
            CREATE TABLE IF NOT EXISTS mark_price_candles (
                exchange TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp_ms INTEGER NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                PRIMARY KEY (exchange, symbol, timeframe, timestamp_ms)
            );
            CREATE TABLE IF NOT EXISTS margin_brackets (
                exchange TEXT NOT NULL,
                symbol TEXT NOT NULL,
                effective_at_ms INTEGER NOT NULL,
                bracket_index INTEGER NOT NULL,
                notional_floor REAL NOT NULL,
                notional_cap REAL NOT NULL,
                maintenance_margin_rate REAL NOT NULL,
                cumulative_maintenance_amount REAL NOT NULL,
                PRIMARY KEY (exchange, symbol, effective_at_ms, bracket_index)
            );
        """)
        return connection

    def upsert_funding_rates(self, rates: list[FundingRate]) -> int:
        if not rates:
            return 0
        with closing(self._connect()) as connection, connection:
            connection.executemany("""
                INSERT INTO funding_rates VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(exchange, symbol, timestamp_ms) DO UPDATE SET
                    rate=excluded.rate, mark_price=excluded.mark_price
            """, [tuple(vars(rate).values()) for rate in rates])
        return len(rates)

    def list_funding_rates(
        self, exchange: str, symbol: str, since_ms: int, until_ms: int
    ) -> list[FundingRate]:
        self._validate_range(symbol, since_ms, until_ms)
        with closing(self._connect()) as connection:
            rows = connection.execute("""
                SELECT exchange, symbol, timestamp_ms, rate, mark_price
                FROM funding_rates
                WHERE exchange=? AND symbol=? AND timestamp_ms>=? AND timestamp_ms<?
                ORDER BY timestamp_ms
            """, (exchange, symbol, since_ms, until_ms)).fetchall()
        return [FundingRate(**dict(row)) for row in rows]

    def upsert_mark_prices(self, candles: list[MarkPriceCandle]) -> int:
        if not candles:
            return 0
        columns = (
            "exchange", "symbol", "timeframe", "timestamp_ms",
            "open", "high", "low", "close",
        )
        with closing(self._connect()) as connection, connection:
            connection.executemany("""
                INSERT INTO mark_price_candles VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(exchange, symbol, timeframe, timestamp_ms) DO UPDATE SET
                    open=excluded.open, high=excluded.high,
                    low=excluded.low, close=excluded.close
            """, [tuple(getattr(candle, column) for column in columns) for candle in candles])
        return len(candles)

    def list_mark_prices(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        since_ms: int,
        until_ms: int,
    ) -> list[MarkPriceCandle]:
        self._validate_range(symbol, since_ms, until_ms)
        with closing(self._connect()) as connection:
            rows = connection.execute("""
                SELECT exchange, symbol, timestamp_ms, open, high, low, close, timeframe
                FROM mark_price_candles
                WHERE exchange=? AND symbol=? AND timeframe=?
                  AND timestamp_ms>=? AND timestamp_ms<?
                ORDER BY timestamp_ms
            """, (exchange, symbol, timeframe, since_ms, until_ms)).fetchall()
        return [MarkPriceCandle(**dict(row)) for row in rows]

    def save_margin_brackets(
        self,
        exchange: str,
        symbol: str,
        effective_at_ms: int,
        brackets: list[MarginBracket],
    ) -> int:
        if symbol not in SYMBOLS or effective_at_ms < 0 or not brackets:
            raise ValueError("invalid margin bracket snapshot")
        MaintenanceMarginModel(brackets)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "DELETE FROM margin_brackets WHERE exchange=? AND symbol=? AND effective_at_ms=?",
                (exchange, symbol, effective_at_ms),
            )
            connection.executemany("""
                INSERT INTO margin_brackets VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    exchange, symbol, effective_at_ms, index,
                    bracket.notional_floor, bracket.notional_cap,
                    bracket.maintenance_margin_rate,
                    bracket.cumulative_maintenance_amount,
                )
                for index, bracket in enumerate(brackets)
            ])
        return len(brackets)

    def latest_margin_model(
        self, exchange: str, symbol: str, at_ms: int
    ) -> tuple[int, MaintenanceMarginModel] | None:
        if symbol not in SYMBOLS or at_ms < 0:
            raise ValueError("invalid margin bracket query")
        with closing(self._connect()) as connection:
            row = connection.execute("""
                SELECT MAX(effective_at_ms) AS effective_at_ms
                FROM margin_brackets
                WHERE exchange=? AND symbol=? AND effective_at_ms<=?
            """, (exchange, symbol, at_ms)).fetchone()
            if row["effective_at_ms"] is None:
                return None
            effective_at_ms = int(row["effective_at_ms"])
            rows = connection.execute("""
                SELECT notional_floor, notional_cap, maintenance_margin_rate,
                       cumulative_maintenance_amount
                FROM margin_brackets
                WHERE exchange=? AND symbol=? AND effective_at_ms=?
                ORDER BY bracket_index
            """, (exchange, symbol, effective_at_ms)).fetchall()
        return effective_at_ms, MaintenanceMarginModel([
            MarginBracket(**dict(item)) for item in rows
        ])

    @staticmethod
    def _validate_range(symbol: str, since_ms: int, until_ms: int) -> None:
        if symbol not in SYMBOLS or since_ms < 0 or until_ms <= since_ms:
            raise ValueError("invalid derivatives data range")
