from contextlib import closing
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from time import time

from app.backtest.models import BacktestConfig, BacktestResult
from app.data.models import Candle


@dataclass(frozen=True)
class BacktestRun:
    run_key: str
    created_at_ms: int
    stage: str
    note: str
    strategy_name: str
    symbol: str
    timeframe: str
    since_ms: int
    until_ms: int
    fast_period: int | None
    slow_period: int | None
    initial_cash: float
    fee_bps: float
    slippage_bps: float
    stop_loss_pct: float | None
    take_profit_pct: float | None
    leverage: float
    candle_count: int
    data_fingerprint: str
    final_equity: float
    total_return: float
    cagr: float
    sharpe_ratio: float
    sortino_ratio: float
    maximum_drawdown: float
    number_of_trades: int
    exposure: float
    fees: float
    slippage: float


@dataclass(frozen=True)
class StrategyAdjustmentLog:
    adjustment_key: str
    created_at_ms: int
    run_key: str
    previous_run_key: str | None
    strategy_family: str
    version_number: int
    symbol: str
    timeframe: str
    stage: str
    hypothesis: str
    changes_json: str
    total_return: float
    maximum_drawdown: float
    number_of_trades: int

    @property
    def changes(self) -> dict[str, dict[str, object]]:
        return json.loads(self.changes_json)


@dataclass(frozen=True)
class SavedBacktestRun:
    run: BacktestRun
    created: bool


class BacktestRunRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("""
            CREATE TABLE IF NOT EXISTS backtest_runs (
                run_key TEXT PRIMARY KEY,
                created_at_ms INTEGER NOT NULL,
                stage TEXT NOT NULL,
                note TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                since_ms INTEGER NOT NULL,
                until_ms INTEGER NOT NULL,
                fast_period INTEGER,
                slow_period INTEGER,
                initial_cash REAL NOT NULL,
                fee_bps REAL NOT NULL,
                slippage_bps REAL NOT NULL,
                stop_loss_pct REAL,
                take_profit_pct REAL,
                leverage REAL NOT NULL,
                candle_count INTEGER NOT NULL,
                data_fingerprint TEXT NOT NULL,
                final_equity REAL NOT NULL,
                total_return REAL NOT NULL,
                cagr REAL NOT NULL,
                sharpe_ratio REAL NOT NULL,
                sortino_ratio REAL NOT NULL,
                maximum_drawdown REAL NOT NULL,
                number_of_trades INTEGER NOT NULL,
                exposure REAL NOT NULL,
                fees REAL NOT NULL,
                slippage REAL NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS strategy_adjustment_logs (
                adjustment_key TEXT PRIMARY KEY,
                created_at_ms INTEGER NOT NULL,
                run_key TEXT NOT NULL UNIQUE,
                previous_run_key TEXT,
                strategy_family TEXT NOT NULL,
                version_number INTEGER NOT NULL DEFAULT 0,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                stage TEXT NOT NULL,
                hypothesis TEXT NOT NULL,
                changes_json TEXT NOT NULL,
                total_return REAL NOT NULL,
                maximum_drawdown REAL NOT NULL,
                number_of_trades INTEGER NOT NULL
            )
        """)
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(strategy_adjustment_logs)"
            ).fetchall()
        }
        if "version_number" not in columns:
            connection.execute(
                "ALTER TABLE strategy_adjustment_logs "
                "ADD COLUMN version_number INTEGER NOT NULL DEFAULT 0"
            )
        self._backfill_adjustment_logs(connection)
        self._renumber_adjustment_versions(connection)
        return connection

    def save(
        self,
        result: BacktestResult,
        candles: list[Candle],
        config: BacktestConfig,
        stage: str,
        note: str,
        fast_period: int | None,
        slow_period: int | None,
        base_run_key: str | None = None,
        signal_candles: list[Candle] | None = None,
    ) -> BacktestRun:
        return self.save_with_status(
            result=result,
            candles=candles,
            config=config,
            stage=stage,
            note=note,
            fast_period=fast_period,
            slow_period=slow_period,
            base_run_key=base_run_key,
            signal_candles=signal_candles,
        ).run

    def save_with_status(
        self,
        result: BacktestResult,
        candles: list[Candle],
        config: BacktestConfig,
        stage: str,
        note: str,
        fast_period: int | None,
        slow_period: int | None,
        base_run_key: str | None = None,
        signal_candles: list[Candle] | None = None,
    ) -> SavedBacktestRun:
        fingerprint = _fingerprint(signal_candles or candles)
        identity = json.dumps(
            {
                "strategy": result.strategy_name,
                "symbol": result.symbol,
                "timeframe": result.timeframe,
                "since": candles[0].timestamp_ms,
                "until": candles[-1].timestamp_ms,
                "fast": fast_period,
                "slow": slow_period,
                "initial_cash": config.initial_cash,
                "fee_bps": config.fee_bps,
                "slippage_bps": config.slippage_bps,
                "stop_loss_pct": config.stop_loss_pct,
                "take_profit_pct": config.take_profit_pct,
                "leverage": config.leverage,
                "stage": stage,
                "data": fingerprint,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        metrics = result.metrics
        run = BacktestRun(
            run_key=sha256(identity.encode()).hexdigest(),
            created_at_ms=int(time() * 1000),
            stage=stage,
            note=note.strip(),
            strategy_name=result.strategy_name,
            symbol=result.symbol,
            timeframe=result.timeframe,
            since_ms=candles[0].timestamp_ms,
            until_ms=candles[-1].timestamp_ms,
            fast_period=fast_period,
            slow_period=slow_period,
            initial_cash=config.initial_cash,
            fee_bps=config.fee_bps,
            slippage_bps=config.slippage_bps,
            stop_loss_pct=config.stop_loss_pct,
            take_profit_pct=config.take_profit_pct,
            leverage=config.leverage,
            candle_count=len(candles),
            data_fingerprint=fingerprint,
            final_equity=result.final_equity,
            total_return=metrics.total_return,
            cagr=metrics.cagr,
            sharpe_ratio=metrics.sharpe_ratio,
            sortino_ratio=metrics.sortino_ratio,
            maximum_drawdown=metrics.maximum_drawdown,
            number_of_trades=metrics.number_of_trades,
            exposure=metrics.exposure,
            fees=metrics.fees,
            slippage=metrics.slippage,
        )
        with closing(self._connect()) as connection:
            with connection:
                existing = connection.execute(
                    "SELECT * FROM backtest_runs WHERE run_key=?", (run.run_key,)
                ).fetchone()
                if existing is not None:
                    return SavedBacktestRun(
                        run=BacktestRun(**dict(existing)),
                        created=False,
                    )
                previous = self._comparison_run(connection, run, base_run_key)
                columns = tuple(vars(run))
                placeholders = ", ".join("?" for _ in columns)
                connection.execute(
                    f"INSERT INTO backtest_runs ({', '.join(columns)}) "
                    f"VALUES ({placeholders})",
                    tuple(vars(run).values()),
                )
                self._insert_adjustment_log(connection, run, previous)
        return SavedBacktestRun(run=run, created=True)

    def list_recent(self, limit: int = 20) -> list[BacktestRun]:
        if not 1 <= limit <= 100:
            raise ValueError("invalid backtest run limit")
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM backtest_runs ORDER BY created_at_ms DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [BacktestRun(**dict(row)) for row in rows]

    def list_adjustments(self, limit: int = 50) -> list[StrategyAdjustmentLog]:
        if not 1 <= limit <= 200:
            raise ValueError("invalid strategy adjustment limit")
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM strategy_adjustment_logs "
                "ORDER BY created_at_ms DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [StrategyAdjustmentLog(**dict(row)) for row in rows]

    def get_run(self, run_key: str) -> BacktestRun | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM backtest_runs WHERE run_key=?", (run_key,)
            ).fetchone()
        return BacktestRun(**dict(row)) if row is not None else None

    @classmethod
    def _backfill_adjustment_logs(cls, connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            "SELECT * FROM backtest_runs ORDER BY created_at_ms ASC"
        ).fetchall()
        previous_by_series: dict[tuple[str, str, str], BacktestRun] = {}
        with connection:
            for row in rows:
                run = BacktestRun(**dict(row))
                family = "sma" if run.fast_period is not None else "buy-hold"
                series = (run.symbol, run.timeframe, family)
                exists = connection.execute(
                    "SELECT 1 FROM strategy_adjustment_logs WHERE run_key=?",
                    (run.run_key,),
                ).fetchone()
                if exists is None:
                    cls._insert_adjustment_log(
                        connection, run, previous_by_series.get(series)
                    )
                previous_by_series[series] = run

    @staticmethod
    def _renumber_adjustment_versions(connection: sqlite3.Connection) -> None:
        rows = connection.execute("""
            SELECT adjustment_key, symbol, timeframe, strategy_family
            FROM strategy_adjustment_logs
            ORDER BY created_at_ms ASC, adjustment_key ASC
        """).fetchall()
        counters: dict[tuple[str, str, str], int] = {}
        with connection:
            for row in rows:
                series = (row["symbol"], row["timeframe"], row["strategy_family"])
                counters[series] = counters.get(series, 0) + 1
                connection.execute(
                    "UPDATE strategy_adjustment_logs SET version_number=? "
                    "WHERE adjustment_key=?",
                    (counters[series], row["adjustment_key"]),
                )

    @staticmethod
    def _comparison_run(
        connection: sqlite3.Connection,
        run: BacktestRun,
        base_run_key: str | None,
    ) -> BacktestRun | None:
        if base_run_key:
            row = connection.execute(
                "SELECT * FROM backtest_runs WHERE run_key=?", (base_run_key,)
            ).fetchone()
            if row is None:
                raise ValueError("selected base strategy version does not exist")
            selected = BacktestRun(**dict(row))
            same_family = (selected.fast_period is None) == (run.fast_period is None)
            if (
                selected.symbol != run.symbol
                or selected.timeframe != run.timeframe
                or not same_family
            ):
                raise ValueError("selected base version belongs to another strategy series")
            return selected
        row = connection.execute("""
            SELECT * FROM backtest_runs
            WHERE symbol=? AND timeframe=? AND run_key<>?
              AND ((? IS NULL AND fast_period IS NULL)
                   OR (? IS NOT NULL AND fast_period IS NOT NULL))
            ORDER BY created_at_ms DESC LIMIT 1
        """, (
            run.symbol,
            run.timeframe,
            run.run_key,
            run.fast_period,
            run.fast_period,
        )).fetchone()
        return BacktestRun(**dict(row)) if row is not None else None

    @staticmethod
    def _insert_adjustment_log(
        connection: sqlite3.Connection,
        run: BacktestRun,
        previous: BacktestRun | None,
    ) -> None:
        family = "sma" if run.fast_period is not None else "buy-hold"
        changes = _parameter_changes(previous, run)
        version_number = connection.execute("""
            SELECT COALESCE(MAX(version_number), 0) + 1
            FROM strategy_adjustment_logs
            WHERE symbol=? AND timeframe=? AND strategy_family=?
        """, (run.symbol, run.timeframe, family)).fetchone()[0]
        log = StrategyAdjustmentLog(
            adjustment_key=sha256(f"adjustment:{run.run_key}".encode()).hexdigest(),
            created_at_ms=run.created_at_ms,
            run_key=run.run_key,
            previous_run_key=previous.run_key if previous else None,
            strategy_family=family,
            version_number=int(version_number),
            symbol=run.symbol,
            timeframe=run.timeframe,
            stage=run.stage,
            hypothesis=run.note,
            changes_json=json.dumps(changes, ensure_ascii=False, sort_keys=True),
            total_return=run.total_return,
            maximum_drawdown=run.maximum_drawdown,
            number_of_trades=run.number_of_trades,
        )
        columns = tuple(vars(log))
        connection.execute(
            f"INSERT INTO strategy_adjustment_logs ({', '.join(columns)}) "
            f"VALUES ({', '.join('?' for _ in columns)})",
            tuple(vars(log).values()),
        )


def _fingerprint(candles: list[Candle]) -> str:
    digest = sha256()
    for candle in candles:
        digest.update(
            (
                f"{candle.timestamp_ms}|{candle.open:.12g}|{candle.high:.12g}|"
                f"{candle.low:.12g}|{candle.close:.12g}|{candle.volume:.12g}\n"
            ).encode()
        )
    return digest.hexdigest()


def _parameter_changes(
    previous: BacktestRun | None, current: BacktestRun
) -> dict[str, dict[str, object]]:
    fields = (
        "since_ms",
        "until_ms",
        "fast_period",
        "slow_period",
        "initial_cash",
        "fee_bps",
        "slippage_bps",
        "stop_loss_pct",
        "take_profit_pct",
        "leverage",
        "stage",
        "data_fingerprint",
    )
    if previous is None:
        return {}
    return {
        field: {"from": getattr(previous, field), "to": getattr(current, field)}
        for field in fields
        if getattr(previous, field) != getattr(current, field)
    }
