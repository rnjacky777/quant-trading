"""Persist human-requested pair reviews separately from version optimization."""
from contextlib import closing
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
from time import time

from app.backtest.comparison import load_comparison, comparison_warnings


class ComparisonReviewRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS comparison_reviews (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pair_key TEXT NOT NULL, requested_at_ms INTEGER NOT NULL,
                status TEXT NOT NULL, objective TEXT NOT NULL,
                evidence_json TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '',
                processed_at_ms INTEGER
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_pending_pair_review
            ON comparison_reviews(pair_key) WHERE status='pending';
        """)
        return connection

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict:
        item = dict(row)
        item["evidence"] = json.loads(item.pop("evidence_json"))
        item["run_keys"] = [entry["run"]["run_key"] for entry in item["evidence"]["entries"]]
        return item

    def enqueue(self, exchange: str, keys: list[str], objective: str = "") -> dict:
        entries = load_comparison(self.path, exchange, keys)
        evidence = dict(entries=[dict(run=asdict(entry.run), version=entry.version,
                                     metrics=asdict(entry.result.metrics) if entry.result else None,
                                     source=entry.source, error=entry.error) for entry in entries],
                        warnings=comparison_warnings(entries))
        # Nonfinite metric values are explicit strings, never invalid JSON numbers.
        def clean(value):
            if isinstance(value, float):
                from math import isfinite
                return value if isfinite(value) else str(value)
            if isinstance(value, dict):
                return {key: clean(item) for key, item in value.items()}
            if isinstance(value, list):
                return [clean(item) for item in value]
            return value
        pair = ":".join(sorted(keys))
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT * FROM comparison_reviews WHERE pair_key=? AND status='pending'", (pair,)).fetchone()
            if existing:
                return self._decode(existing)
            cursor = connection.execute("INSERT INTO comparison_reviews(pair_key,requested_at_ms,status,objective,evidence_json) VALUES(?,?,'pending',?,?)",
                                        (pair, int(time()*1000), objective.strip()[:1000], json.dumps(clean(evidence), ensure_ascii=False, allow_nan=False)))
            row = connection.execute("SELECT * FROM comparison_reviews WHERE request_id=?", (cursor.lastrowid,)).fetchone()
            return self._decode(row)

    def list_requests(self, pending_only: bool = False) -> list[dict]:
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT * FROM comparison_reviews " + ("WHERE status='pending' " if pending_only else "") + "ORDER BY request_id DESC").fetchall()
            return [self._decode(row) for row in rows]

    def for_pair(self, keys: list[str]) -> list[dict]:
        pair = ":".join(sorted(keys))
        return [item for item in self.list_requests() if item["pair_key"] == pair]

    def get(self, request_id: int) -> dict | None:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT * FROM comparison_reviews WHERE request_id=?", (request_id,)).fetchone()
            return self._decode(row) if row else None

    def finish(self, request_id: int, status: str, summary: str) -> None:
        if status not in {"completed", "cancelled"} or not summary.strip():
            raise ValueError("審查狀態或判斷內容無效")
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute("UPDATE comparison_reviews SET status=?,summary=?,processed_at_ms=? WHERE request_id=? AND status='pending'",
                                        (status, summary.strip(), int(time()*1000), request_id))
            if cursor.rowcount != 1:
                raise ValueError("任務不存在或已處理，不能覆寫判斷")
