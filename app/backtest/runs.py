from contextlib import closing
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from time import time
from math import isclose

from app.backtest.models import BacktestConfig, BacktestResult
from app.backtest.configuration import saved_policy, strategy_family
from app.backtest.research import ResearchPlanRepository
from app.backtest.results import serialize_result, deserialize_result
from app.data.models import Candle, TIMEFRAMES_MS


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
    strategy_key: str | None = None
    policy_json: str = "{}"
    research_plan_id: str = ""


@dataclass(frozen=True)
class StrategyVersion:
    strategy_key: str
    created_at_ms: int
    version_number: int
    previous_strategy_key: str | None
    strategy_family: str
    symbol: str
    timeframe: str
    fast_period: int | None
    slow_period: int | None
    stop_loss_pct: float | None
    take_profit_pct: float | None
    leverage: float
    hypothesis: str
    policy_json: str = "{}"


@dataclass(frozen=True)
class StrategyAdjustmentLog:
    """Legacy per-run audit record kept for backwards compatibility."""

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
    strategy_created: bool = False


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
                slippage REAL NOT NULL,
                strategy_key TEXT
            )
        """)
        run_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(backtest_runs)").fetchall()
        }
        if "strategy_key" not in run_columns:
            connection.execute("ALTER TABLE backtest_runs ADD COLUMN strategy_key TEXT")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS strategy_versions (
                strategy_key TEXT PRIMARY KEY,
                created_at_ms INTEGER NOT NULL,
                version_number INTEGER NOT NULL,
                previous_strategy_key TEXT,
                strategy_family TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                fast_period INTEGER,
                slow_period INTEGER,
                stop_loss_pct REAL,
                take_profit_pct REAL,
                leverage REAL NOT NULL,
                hypothesis TEXT NOT NULL,
                UNIQUE(symbol, timeframe, strategy_family, version_number)
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
        adjustment_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(strategy_adjustment_logs)"
            ).fetchall()
        }
        if "version_number" not in adjustment_columns:
            connection.execute(
                "ALTER TABLE strategy_adjustment_logs "
                "ADD COLUMN version_number INTEGER NOT NULL DEFAULT 0"
            )
        for table, fields in {
            "backtest_runs": {"policy_json": "'{}'", "research_plan_id": "''"},
            "strategy_versions": {"policy_json": "'{}'"},
        }.items():
            columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
            for field, default in fields.items():
                if field not in columns:
                    connection.execute(f"ALTER TABLE {table} ADD COLUMN {field} TEXT NOT NULL DEFAULT {default}")
        connection.execute("""CREATE TABLE IF NOT EXISTS backtest_results (
            run_key TEXT PRIMARY KEY, saved_at_ms INTEGER NOT NULL,
            source TEXT NOT NULL, payload_json TEXT NOT NULL,
            FOREIGN KEY(run_key) REFERENCES backtest_runs(run_key)
        )""")
        self._backfill_strategy_versions(connection)
        self._backfill_adjustment_logs(connection)
        self._sync_adjustment_versions(connection)
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
        research_plan_id: str = "",
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
            research_plan_id=research_plan_id,
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
        research_plan_id: str = "",
    ) -> SavedBacktestRun:
        if stage not in {"development", "validation", "out_of_sample"}:
            raise ValueError("invalid research stage")
        if stage == "out_of_sample" and not research_plan_id:
            raise ValueError("out_of_sample requires a preregistered research plan")
        fingerprint = _fingerprint(signal_candles or candles)
        family = strategy_family(result.strategy_name)
        policy_json = saved_policy(config, result.strategy_name)
        strategy_key = _strategy_key(
            result.symbol,
            result.timeframe,
            family,
            fast_period,
            slow_period,
            config.stop_loss_pct,
            config.take_profit_pct,
            config.leverage,
            policy_json,
        )
        identity_values = {
                "strategy": result.strategy_name,
                "symbol": result.symbol,
                "timeframe": result.timeframe,
                "since": candles[0].timestamp_ms,
                "until": candles[-1].timestamp_ms,
                "fast": fast_period,
                "slow": slow_period,
                "initial_cash": float(config.initial_cash),
                "fee_bps": float(config.fee_bps),
                "slippage_bps": float(config.slippage_bps),
                "stop_loss_pct": float(config.stop_loss_pct) if config.stop_loss_pct is not None else None,
                "take_profit_pct": float(config.take_profit_pct) if config.take_profit_pct is not None else None,
                "leverage": float(config.leverage),
                "stage": stage,
                "data": fingerprint,
            }
        if policy_json != "{}":
            identity_values["policy"] = json.loads(policy_json)
        if research_plan_id:
            identity_values["research_plan_id"] = research_plan_id
        identity = json.dumps(
            identity_values,
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
            strategy_key=strategy_key,
            policy_json=policy_json,
            research_plan_id=research_plan_id,
        )
        if research_plan_id:
            ResearchPlanRepository(self.path).list_plans()
        with closing(self._connect()) as connection:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                if research_plan_id:
                    ResearchPlanRepository.validate_on_connection(
                        connection, research_plan_id, stage, candles[0].timestamp_ms,
                        candles[-1].timestamp_ms + TIMEFRAMES_MS[result.timeframe], consume=True,
                    )
                existing = connection.execute(
                    "SELECT * FROM backtest_runs WHERE run_key=?", (run.run_key,)
                ).fetchone()
                if existing is not None:
                    self._store_result(connection, BacktestRun(**dict(existing)), result, "reproduced")
                    return SavedBacktestRun(
                        run=BacktestRun(**dict(existing)), created=False
                    )
                previous = self._comparison_run(connection, run, base_run_key)
                strategy_created = connection.execute(
                    "SELECT 1 FROM strategy_versions WHERE strategy_key=?",
                    (strategy_key,),
                ).fetchone() is None
                version = self._ensure_strategy_version(
                    connection, run, family, base_run_key
                )
                columns = tuple(vars(run))
                connection.execute(
                    f"INSERT INTO backtest_runs ({', '.join(columns)}) "
                    f"VALUES ({', '.join('?' for _ in columns)})",
                    tuple(vars(run).values()),
                )
                self._insert_adjustment_log(connection, run, previous, version)
                self._store_result(connection, run, result, "original")
        return SavedBacktestRun(
            run=run,
            created=True,
            strategy_created=strategy_created,
        )

    @staticmethod
    def _store_result(
        connection: sqlite3.Connection, run: BacktestRun, result: BacktestResult, source: str,
    ) -> None:
        if (run.symbol, run.timeframe, run.strategy_name) != (result.symbol, result.timeframe, result.strategy_name):
            raise ValueError("result identity does not match saved experiment")
        for field in ("initial_cash", "final_equity"):
            if not isclose(getattr(run, field), getattr(result, field), rel_tol=1e-10, abs_tol=1e-8):
                raise ValueError("result does not match saved experiment")
        metric_fields = ("total_return", "cagr", "sharpe_ratio", "sortino_ratio", "maximum_drawdown",
                         "number_of_trades", "exposure", "fees", "slippage")
        if any(not isclose(getattr(run, field), getattr(result.metrics, field), rel_tol=1e-10, abs_tol=1e-8) for field in metric_fields):
            raise ValueError("result metrics do not match saved experiment")
        curve = result.equity_curve
        if not curve or not isclose(curve[0].equity, run.initial_cash) or not isclose(curve[-1].equity, run.final_equity):
            raise ValueError("equity curve does not match saved experiment")
        if curve[-1].timestamp_ms != run.until_ms or any(b.timestamp_ms <= a.timestamp_ms for a, b in zip(curve, curve[1:])):
            raise ValueError("invalid equity curve timestamps")
        connection.execute("INSERT OR IGNORE INTO backtest_results VALUES (?,?,?,?)",
                           (run.run_key, int(time()*1000), source, serialize_result(result)))

    def get_result(self, run_key: str) -> tuple[BacktestResult, str] | None:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT payload_json,source FROM backtest_results WHERE run_key=?", (run_key,)).fetchone()
        return (deserialize_result(row["payload_json"]), row["source"]) if row else None

    def list_matching_period(self, run: BacktestRun) -> list[BacktestRun]:
        """Find other strategy versions with exactly the same evaluation window."""
        with closing(self._connect()) as connection:
            rows = connection.execute("""SELECT * FROM backtest_runs
                WHERE symbol=? AND timeframe=? AND since_ms=? AND until_ms=?
                  AND strategy_key<>? ORDER BY created_at_ms DESC,run_key DESC""",
                (run.symbol, run.timeframe, run.since_ms, run.until_ms, run.strategy_key),
            ).fetchall()
        return [BacktestRun(**dict(row)) for row in rows]

    def list_periods(self, symbol: str, timeframe: str) -> list[dict[str, int]]:
        interval = TIMEFRAMES_MS[timeframe]
        with closing(self._connect()) as connection:
            rows = connection.execute("""SELECT since_ms,until_ms+? AS until_exclusive_ms,
                COUNT(*) AS run_count,MAX(created_at_ms) AS latest_at
                FROM backtest_runs WHERE symbol=? AND timeframe=?
                GROUP BY since_ms,until_ms ORDER BY latest_at DESC,since_ms DESC""",
                (interval, symbol, timeframe)).fetchall()
        return [dict(row) for row in rows]

    def list_runs_in_period(self, symbol: str, timeframe: str, since_ms: int, until_exclusive_ms: int) -> list[BacktestRun]:
        with closing(self._connect()) as connection:
            rows = connection.execute("""SELECT * FROM backtest_runs
                WHERE symbol=? AND timeframe=? AND since_ms=? AND until_ms=?
                ORDER BY created_at_ms DESC,run_key DESC""",
                (symbol, timeframe, since_ms, until_exclusive_ms-TIMEFRAMES_MS[timeframe])).fetchall()
        return [BacktestRun(**dict(row)) for row in rows]

    def save_reproduced_result(self, run_key: str, result: BacktestResult) -> None:
        with closing(self._connect()) as connection, connection:
            row = connection.execute("SELECT * FROM backtest_runs WHERE run_key=?", (run_key,)).fetchone()
            if row is None:
                raise ValueError("saved experiment does not exist")
            self._store_result(connection, BacktestRun(**dict(row)), result, "reproduced")

    def list_recent(self, limit: int = 20) -> list[BacktestRun]:
        if not 1 <= limit <= 100:
            raise ValueError("invalid backtest run limit")
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM backtest_runs ORDER BY created_at_ms DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [BacktestRun(**dict(row)) for row in rows]

    def list_strategy_versions(self, limit: int = 100) -> list[StrategyVersion]:
        if not 1 <= limit <= 500:
            raise ValueError("invalid strategy version limit")
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM strategy_versions "
                "ORDER BY created_at_ms DESC, version_number DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [StrategyVersion(**dict(row)) for row in rows]

    def get_strategy_version(self, strategy_key: str) -> StrategyVersion | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM strategy_versions WHERE strategy_key=?",
                (strategy_key,),
            ).fetchone()
        return StrategyVersion(**dict(row)) if row is not None else None

    def get_strategy_version_for_run(self, run_key: str) -> StrategyVersion | None:
        with closing(self._connect()) as connection:
            row = connection.execute("""
                SELECT version.* FROM strategy_versions AS version
                JOIN backtest_runs AS run ON run.strategy_key=version.strategy_key
                WHERE run.run_key=?
            """, (run_key,)).fetchone()
        return StrategyVersion(**dict(row)) if row is not None else None

    def list_runs_for_strategy(
        self, strategy_key: str, limit: int | None = 100
    ) -> list[BacktestRun]:
        if limit is not None and not 1 <= limit <= 500:
            raise ValueError("invalid strategy run limit")
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM backtest_runs WHERE strategy_key=? "
                "ORDER BY created_at_ms DESC,run_key DESC" + (" LIMIT ?" if limit is not None else ""),
                (strategy_key, limit) if limit is not None else (strategy_key,),
            ).fetchall()
        return [BacktestRun(**dict(row)) for row in rows]

    def get_latest_run_for_strategy(
        self, strategy_key: str, stage: str | None = None
    ) -> BacktestRun | None:
        query = "SELECT * FROM backtest_runs WHERE strategy_key=?"
        params: tuple[object, ...]
        if stage is None:
            params = (strategy_key,)
        else:
            query += " AND stage=?"
            params = (strategy_key, stage)
        query += " ORDER BY created_at_ms DESC LIMIT 1"
        with closing(self._connect()) as connection:
            row = connection.execute(query, params).fetchone()
        return BacktestRun(**dict(row)) if row is not None else None

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
    def _backfill_strategy_versions(cls, connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            "SELECT * FROM backtest_runs ORDER BY created_at_ms ASC, run_key ASC"
        ).fetchall()
        with connection:
            for row in rows:
                run = BacktestRun(**dict(row))
                family = strategy_family(run.strategy_name)
                key = _strategy_key(
                    run.symbol,
                    run.timeframe,
                    family,
                    run.fast_period,
                    run.slow_period,
                    run.stop_loss_pct,
                    run.take_profit_pct,
                    run.leverage,
                    run.policy_json,
                )
                existing = connection.execute(
                    "SELECT 1 FROM strategy_versions WHERE strategy_key=?", (key,)
                ).fetchone()
                if existing is None:
                    previous_key = cls._migration_previous_strategy_key(
                        connection, run, family
                    )
                    version_number = connection.execute("""
                        SELECT COALESCE(MAX(version_number), 0) + 1
                        FROM strategy_versions
                        WHERE symbol=? AND timeframe=? AND strategy_family=?
                    """, (run.symbol, run.timeframe, family)).fetchone()[0]
                    connection.execute(
                        "INSERT INTO strategy_versions VALUES "
                        "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            key,
                            run.created_at_ms,
                            int(version_number),
                            previous_key,
                            family,
                            run.symbol,
                            run.timeframe,
                            run.fast_period,
                            run.slow_period,
                            run.stop_loss_pct,
                            run.take_profit_pct,
                            run.leverage,
                            run.note,
                            run.policy_json,
                        ),
                    )
                connection.execute(
                    "UPDATE backtest_runs SET strategy_key=? WHERE run_key=?",
                    (key, run.run_key),
                )

    @staticmethod
    def _migration_previous_strategy_key(
        connection: sqlite3.Connection, run: BacktestRun, family: str
    ) -> str | None:
        adjustment = connection.execute(
            "SELECT previous_run_key FROM strategy_adjustment_logs WHERE run_key=?",
            (run.run_key,),
        ).fetchone()
        if adjustment is not None and adjustment["previous_run_key"]:
            previous = connection.execute(
                "SELECT strategy_key FROM backtest_runs WHERE run_key=?",
                (adjustment["previous_run_key"],),
            ).fetchone()
            if previous is not None and previous["strategy_key"]:
                return str(previous["strategy_key"])
        latest = connection.execute("""
            SELECT strategy_key FROM strategy_versions
            WHERE symbol=? AND timeframe=? AND strategy_family=?
            ORDER BY version_number DESC LIMIT 1
        """, (run.symbol, run.timeframe, family)).fetchone()
        return str(latest["strategy_key"]) if latest is not None else None

    @classmethod
    def _backfill_adjustment_logs(cls, connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            "SELECT * FROM backtest_runs ORDER BY created_at_ms ASC"
        ).fetchall()
        previous_by_series: dict[tuple[str, str, str], BacktestRun] = {}
        with connection:
            for row in rows:
                run = BacktestRun(**dict(row))
                family = strategy_family(run.strategy_name)
                series = (run.symbol, run.timeframe, family)
                exists = connection.execute(
                    "SELECT 1 FROM strategy_adjustment_logs WHERE run_key=?",
                    (run.run_key,),
                ).fetchone()
                if exists is None:
                    version_row = connection.execute(
                        "SELECT * FROM strategy_versions WHERE strategy_key=?",
                        (run.strategy_key,),
                    ).fetchone()
                    if version_row is None:
                        raise ValueError("strategy version migration failed")
                    cls._insert_adjustment_log(
                        connection,
                        run,
                        previous_by_series.get(series),
                        StrategyVersion(**dict(version_row)),
                    )
                previous_by_series[series] = run

    @staticmethod
    def _sync_adjustment_versions(connection: sqlite3.Connection) -> None:
        with connection:
            connection.execute("""
                UPDATE strategy_adjustment_logs
                SET version_number = COALESCE((
                    SELECT version.version_number
                    FROM backtest_runs AS run
                    JOIN strategy_versions AS version
                      ON version.strategy_key=run.strategy_key
                    WHERE run.run_key=strategy_adjustment_logs.run_key
                ), version_number)
            """)

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
            same_family = strategy_family(selected.strategy_name) == strategy_family(run.strategy_name)
            if (
                selected.symbol != run.symbol
                or selected.timeframe != run.timeframe
                or not same_family
            ):
                raise ValueError("selected base version belongs to another strategy series")
            return selected
        rows = connection.execute("""
            SELECT * FROM backtest_runs
            WHERE symbol=? AND timeframe=? AND run_key<>?
            ORDER BY created_at_ms DESC
        """, (
            run.symbol,
            run.timeframe,
            run.run_key,
        )).fetchall()
        return next((BacktestRun(**dict(row)) for row in rows
                     if strategy_family(row["strategy_name"]) == strategy_family(run.strategy_name)), None)

    @staticmethod
    def _ensure_strategy_version(
        connection: sqlite3.Connection,
        run: BacktestRun,
        family: str,
        base_run_key: str | None,
    ) -> StrategyVersion:
        existing = connection.execute(
            "SELECT * FROM strategy_versions WHERE strategy_key=?",
            (run.strategy_key,),
        ).fetchone()
        if existing is not None:
            return StrategyVersion(**dict(existing))
        previous_key: str | None = None
        if base_run_key:
            base = connection.execute(
                "SELECT strategy_key FROM backtest_runs WHERE run_key=?",
                (base_run_key,),
            ).fetchone()
            if base is None:
                raise ValueError("selected base strategy version does not exist")
            previous_key = base["strategy_key"]
        if previous_key is None:
            latest = connection.execute("""
                SELECT strategy_key FROM strategy_versions
                WHERE symbol=? AND timeframe=? AND strategy_family=?
                ORDER BY version_number DESC LIMIT 1
            """, (run.symbol, run.timeframe, family)).fetchone()
            previous_key = latest["strategy_key"] if latest is not None else None
        version_number = connection.execute("""
            SELECT COALESCE(MAX(version_number), 0) + 1
            FROM strategy_versions
            WHERE symbol=? AND timeframe=? AND strategy_family=?
        """, (run.symbol, run.timeframe, family)).fetchone()[0]
        version = StrategyVersion(
            strategy_key=str(run.strategy_key),
            created_at_ms=run.created_at_ms,
            version_number=int(version_number),
            previous_strategy_key=previous_key,
            strategy_family=family,
            symbol=run.symbol,
            timeframe=run.timeframe,
            fast_period=run.fast_period,
            slow_period=run.slow_period,
            stop_loss_pct=run.stop_loss_pct,
            take_profit_pct=run.take_profit_pct,
            leverage=run.leverage,
            hypothesis=run.note,
            policy_json=run.policy_json,
        )
        columns = tuple(vars(version))
        connection.execute(
            f"INSERT INTO strategy_versions ({', '.join(columns)}) "
            f"VALUES ({', '.join('?' for _ in columns)})",
            tuple(vars(version).values()),
        )
        return version

    @staticmethod
    def _insert_adjustment_log(
        connection: sqlite3.Connection,
        run: BacktestRun,
        previous: BacktestRun | None,
        version: StrategyVersion,
    ) -> None:
        changes = _parameter_changes(previous, run)
        log = StrategyAdjustmentLog(
            adjustment_key=sha256(f"adjustment:{run.run_key}".encode()).hexdigest(),
            created_at_ms=run.created_at_ms,
            run_key=run.run_key,
            previous_run_key=previous.run_key if previous else None,
            strategy_family=version.strategy_family,
            version_number=version.version_number,
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


def _strategy_key(
    symbol: str,
    timeframe: str,
    family: str,
    fast_period: int | None,
    slow_period: int | None,
    stop_loss_pct: float | None,
    take_profit_pct: float | None,
    leverage: float,
    policy_json: str = "{}",
) -> str:
    values = {
            "symbol": symbol,
            "timeframe": timeframe,
            "family": family,
            "fast_period": fast_period,
            "slow_period": slow_period,
            "stop_loss_pct": float(stop_loss_pct) if stop_loss_pct is not None else None,
            "take_profit_pct": float(take_profit_pct) if take_profit_pct is not None else None,
            "leverage": float(leverage),
        }
    if policy_json != "{}":
        values["policy"] = json.loads(policy_json)
    identity = json.dumps(
        values,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(identity.encode()).hexdigest()


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
        "fast_period",
        "slow_period",
        "stop_loss_pct",
        "take_profit_pct",
        "leverage",
        "policy_json",
    )
    if previous is None:
        return {}
    return {
        field: {"from": getattr(previous, field), "to": getattr(current, field)}
        for field in fields
        if getattr(previous, field) != getattr(current, field)
    }
