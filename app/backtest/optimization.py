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

    @property
    def changes(self) -> dict[str, object]:
        return json.loads(self.changes_json)


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
        return connection

    def enqueue(self, base_run_key: str, objective: str = "") -> OptimizationRequest:
        self._validate_run_key(base_run_key)
        objective = objective.strip()[:300]
        with closing(self._connect()) as connection, connection:
            existing = connection.execute("""
                SELECT * FROM strategy_optimization_requests
                WHERE base_run_key=? AND status='pending'
            """, (base_run_key,)).fetchone()
            if existing is not None:
                return OptimizationRequest(**dict(existing))
            cursor = connection.execute("""
                INSERT INTO strategy_optimization_requests (
                    base_run_key, requested_at_ms, status, objective, changes_json
                ) VALUES (?, ?, 'pending', ?, '{}')
            """, (base_run_key, int(time() * 1000), objective))
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
    ) -> bool:
        if status not in STATUSES - {"pending"}:
            raise ValueError("invalid final optimization status")
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute("""
                UPDATE strategy_optimization_requests
                SET status=?, processed_at_ms=?, candidate_run_key=?, decision=?,
                    changes_json=?, summary=?, validation_plan=?, error=?
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
                request_id,
            ))
        return cursor.rowcount == 1

    @staticmethod
    def _validate_run_key(run_key: str) -> None:
        if len(run_key) != 64 or any(c not in "0123456789abcdef" for c in run_key):
            raise ValueError("invalid run key")
