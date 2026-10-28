from contextlib import closing
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from time import time


STATUSES = frozenset({"pending", "completed", "skipped", "failed", "cancelled"})


@dataclass(frozen=True)
class OptimizationRequest:
    request_id: int
    base_run_key: str
    requested_at_ms: int
    status: str
    objective: str
    processed_at_ms: int | None
    candidate_run_key: str | None
    decision: str | None
    changes_json: str
    summary: str | None
    validation_plan: str | None
    error: str | None
    strategy_key: str = ""
    evidence_json: str = "[]"
    comparisons_json: str = "[]"

    @property
    def changes(self) -> dict[str, object]:
        return json.loads(self.changes_json)

    @property
    def evidence_run_keys(self) -> list[str]:
        return json.loads(self.evidence_json)


class OptimizationRequestRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS strategy_optimization_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_run_key TEXT NOT NULL,
                requested_at_ms INTEGER NOT NULL,
                status TEXT NOT NULL,
                objective TEXT NOT NULL,
                processed_at_ms INTEGER,
                candidate_run_key TEXT,
                decision TEXT,
                changes_json TEXT NOT NULL DEFAULT '{}',
                summary TEXT,
                validation_plan TEXT,
                error TEXT
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_pending_optimization_per_run
            ON strategy_optimization_requests(base_run_key)
            WHERE status='pending';
        """)
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(strategy_optimization_requests)")}
        for field, default in (("strategy_key", "''"), ("evidence_json", "'[]'"), ("comparisons_json", "'[]'")):
            if field not in columns:
                connection.execute(f"ALTER TABLE strategy_optimization_requests ADD COLUMN {field} TEXT NOT NULL DEFAULT {default}")
        if connection.execute("SELECT 1 FROM sqlite_master WHERE name='backtest_runs'").fetchone():
            for row in connection.execute("SELECT * FROM strategy_optimization_requests WHERE strategy_key=''").fetchall():
                base = connection.execute("SELECT strategy_key FROM backtest_runs WHERE run_key=?", (row["base_run_key"],)).fetchone()
                if base and base["strategy_key"]:
                    keys = [item[0] for item in connection.execute("SELECT run_key FROM backtest_runs WHERE strategy_key=? ORDER BY created_at_ms,run_key", (base["strategy_key"],))]
                    connection.execute("UPDATE strategy_optimization_requests SET strategy_key=?,evidence_json=? WHERE request_id=?",
                                       (base["strategy_key"], json.dumps(keys), row["request_id"]))
        connection.execute("""UPDATE strategy_optimization_requests SET status='cancelled',
            summary='已合併為同版本的等待 AI 優化任務'
            WHERE status='pending' AND strategy_key<>'' AND request_id NOT IN (
              SELECT MIN(request_id) FROM strategy_optimization_requests
              WHERE status='pending' AND strategy_key<>'' GROUP BY strategy_key
            )""")
        connection.execute("""CREATE UNIQUE INDEX IF NOT EXISTS one_pending_optimization_per_strategy
            ON strategy_optimization_requests(strategy_key) WHERE status='pending' AND strategy_key<>''""")
        connection.commit()
        return connection

    def enqueue(self, base_run_key: str, objective: str = "") -> OptimizationRequest:
        self._validate_run_key(base_run_key)
        objective = objective.strip()[:300]
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            strategy_key = ""
            keys = [base_run_key]
            if connection.execute("SELECT 1 FROM sqlite_master WHERE name='backtest_runs'").fetchone():
                base = connection.execute("SELECT strategy_key FROM backtest_runs WHERE run_key=?", (base_run_key,)).fetchone()
                if base:
                    strategy_key = base["strategy_key"] or ""
                    keys = [row[0] for row in connection.execute("SELECT run_key FROM backtest_runs WHERE strategy_key=? ORDER BY created_at_ms,run_key", (strategy_key,))]
            existing = connection.execute("""
                SELECT * FROM strategy_optimization_requests
                WHERE status='pending' AND (base_run_key=? OR (strategy_key<>'' AND strategy_key=?))
            """, (base_run_key, strategy_key)).fetchone()
            if existing is not None:
                connection.execute("UPDATE strategy_optimization_requests SET evidence_json=?,objective=? WHERE request_id=?",
                                   (json.dumps(keys), objective or existing["objective"], existing["request_id"]))
                existing = connection.execute("SELECT * FROM strategy_optimization_requests WHERE request_id=?", (existing["request_id"],)).fetchone()
                return OptimizationRequest(**dict(existing))
            cursor = connection.execute("""
                INSERT INTO strategy_optimization_requests (
                    base_run_key, requested_at_ms, status, objective, changes_json,strategy_key,evidence_json
                ) VALUES (?, ?, 'pending', ?, '{}',?,?)
            """, (base_run_key, int(time() * 1000), objective, strategy_key, json.dumps(keys)))
            row = connection.execute(
                "SELECT * FROM strategy_optimization_requests WHERE request_id=?",
                (cursor.lastrowid,),
            ).fetchone()
        return OptimizationRequest(**dict(row))

    def get(self, request_id: int) -> OptimizationRequest | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM strategy_optimization_requests WHERE request_id=?",
                (request_id,),
            ).fetchone()
        return OptimizationRequest(**dict(row)) if row is not None else None

    def list_requests(
        self, status: str | None = None, limit: int = 100
    ) -> list[OptimizationRequest]:
        if status is not None and status not in STATUSES:
            raise ValueError("invalid optimization status")
        if not 1 <= limit <= 500:
            raise ValueError("invalid optimization request limit")
        query = "SELECT * FROM strategy_optimization_requests"
        params: tuple[object, ...]
        if status is None:
            params = (limit,)
        else:
            query += " WHERE status=?"
            params = (status, limit)
        query += " ORDER BY requested_at_ms DESC, request_id DESC LIMIT ?"
        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()
        return [OptimizationRequest(**dict(row)) for row in rows]

    def enqueue_version(self, strategy_key: str, objective: str = "") -> OptimizationRequest:
        from app.backtest.runs import BacktestRunRepository
        self._validate_run_key(strategy_key)
        runs = BacktestRunRepository(self.path).list_runs_for_strategy(strategy_key, limit=None)
        if not runs:
            raise ValueError("找不到有回測紀錄的策略版本")
        base = next((run for run in runs if run.stage == "development"), runs[0])
        return self.enqueue(base.run_key, objective)

    def cancel(self, request_id: int) -> bool:
        return self._finish(
            request_id,
            status="cancelled",
            decision="cancelled_by_user",
            summary="使用者取消待優化任務",
        )

    def complete(
        self,
        request_id: int,
        *,
        candidate_run_key: str,
        decision: str,
        changes: dict[str, object],
        summary: str,
        validation_plan: str,
        comparisons: list[dict[str, object]] | None = None,
    ) -> bool:
        self._validate_run_key(candidate_run_key)
        return self._finish(
            request_id,
            status="completed",
            candidate_run_key=candidate_run_key,
            decision=decision,
            changes=changes,
            summary=summary,
            validation_plan=validation_plan,
            comparisons=comparisons,
        )

    def skip(
        self,
        request_id: int,
        *,
        decision: str,
        summary: str,
        validation_plan: str,
    ) -> bool:
        return self._finish(
            request_id,
            status="skipped",
            decision=decision,
            summary=summary,
            validation_plan=validation_plan,
        )

    def fail(self, request_id: int, error: str) -> bool:
        return self._finish(
            request_id,
            status="failed",
            decision="execution_failed",
            summary="優化流程執行失敗",
            error=error[:500],
        )

    def _finish(
        self,
        request_id: int,
        *,
        status: str,
        candidate_run_key: str | None = None,
        decision: str | None = None,
        changes: dict[str, object] | None = None,
        summary: str | None = None,
        validation_plan: str | None = None,
        error: str | None = None,
        comparisons: list[dict[str, object]] | None = None,
    ) -> bool:
        if status not in STATUSES - {"pending"}:
            raise ValueError("invalid final optimization status")
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute("""
                UPDATE strategy_optimization_requests
                SET status=?, processed_at_ms=?, candidate_run_key=?, decision=?,
                    changes_json=?, summary=?, validation_plan=?, error=?, comparisons_json=?
                WHERE request_id=? AND status='pending'
            """, (
                status,
                int(time() * 1000),
                candidate_run_key,
                decision,
                json.dumps(changes or {}, ensure_ascii=False, sort_keys=True),
                summary,
                validation_plan,
                error,
                json.dumps(comparisons or [], ensure_ascii=False, allow_nan=False),
                request_id,
            ))
        return cursor.rowcount == 1

    @staticmethod
    def _validate_run_key(run_key: str) -> None:
        if len(run_key) != 64 or any(c not in "0123456789abcdef" for c in run_key):
            raise ValueError("invalid run key")
