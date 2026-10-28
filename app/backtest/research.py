from contextlib import closing
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from time import time

from app.data.models import TIMEFRAMES_MS


@dataclass(frozen=True)
class ResearchPlan:
    plan_id: str
    name: str
    created_at_ms: int
    development_since: int
    development_until: int
    validation_since: int
    validation_until: int
    holdout_since: int
    holdout_until: int
    note: str
    holdout_used: int = 0


class ResearchPlanRepository:
    """Immutable, global research windows; holdout cannot reuse observed dates.

    Conservatively treats every saved historical experiment as observed, across
    symbols/timeframes. Existing validation overlaps are retrospective evidence.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("""CREATE TABLE IF NOT EXISTS research_plans (
            plan_id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at_ms INTEGER NOT NULL,
            development_since INTEGER NOT NULL, development_until INTEGER NOT NULL,
            validation_since INTEGER NOT NULL, validation_until INTEGER NOT NULL,
            holdout_since INTEGER NOT NULL, holdout_until INTEGER NOT NULL,
            note TEXT NOT NULL, holdout_used INTEGER NOT NULL DEFAULT 0
        )""")
        return connection

    def create(
        self, name: str, development_since: int, development_until: int,
        validation_since: int, validation_until: int,
        holdout_since: int, holdout_until: int, note: str = "",
    ) -> ResearchPlan:
        bounds = (development_since, development_until, validation_since,
                  validation_until, holdout_since, holdout_until)
        if not name.strip() or len(name) > 100 or len(note) > 1000:
            raise ValueError("研究計畫名稱或備註無效")
        if any(type(value) is not int or value < 0 or value % TIMEFRAMES_MS["1d"] for value in bounds):
            raise ValueError("研究日期必須為 UTC 日界線")
        if not (development_since < development_until <= validation_since < validation_until <= holdout_since < holdout_until):
            raise ValueError("開發、驗證、保留區間必須依序排列且不可重疊，結束日期不包含當日")
        identity = json.dumps([name.strip(), bounds, note], separators=(",", ":"))
        plan = ResearchPlan(sha256(identity.encode()).hexdigest(), name.strip(), int(time()*1000), *bounds, note)
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_unobserved(connection, holdout_since, holdout_until)
            columns = tuple(asdict(plan))
            connection.execute(
                f"INSERT OR IGNORE INTO research_plans ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                tuple(asdict(plan).values()),
            )
            row = connection.execute("SELECT * FROM research_plans WHERE plan_id=?", (plan.plan_id,)).fetchone()
        return ResearchPlan(**dict(row))

    def list_plans(self) -> list[ResearchPlan]:
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT * FROM research_plans ORDER BY created_at_ms DESC").fetchall()
        return [ResearchPlan(**dict(row)) for row in rows]

    @staticmethod
    def _assert_unobserved(connection: sqlite3.Connection, since: int, until: int) -> None:
        exists = connection.execute("SELECT 1 FROM sqlite_master WHERE name='backtest_runs'").fetchone()
        if exists:
            for row in connection.execute("SELECT since_ms,until_ms,timeframe FROM backtest_runs"):
                if row["since_ms"] < until and row["until_ms"] + TIMEFRAMES_MS[row["timeframe"]] > since:
                    raise ValueError("保留區間與已查看的回測重疊，不能再標為未見資料")

    @classmethod
    def validate_on_connection(
        cls, connection: sqlite3.Connection, plan_id: str, stage: str,
        since: int, until: int, *, consume: bool = False,
    ) -> None:
        row = connection.execute("SELECT * FROM research_plans WHERE plan_id=?", (plan_id,)).fetchone()
        if row is None:
            raise ValueError("研究計畫不存在")
        prefix = {"development": "development", "validation": "validation", "out_of_sample": "holdout"}.get(stage)
        if prefix is None or (since, until) != (row[f"{prefix}_since"], row[f"{prefix}_until"]):
            raise ValueError("回測日期必須完全符合研究計畫所登記的階段區間")
        if prefix == "holdout":
            if row["holdout_used"]:
                raise ValueError("保留區間已查看，不得再作為未見資料使用；請改做探索性回測")
            cls._assert_unobserved(connection, since, until)
            if consume:
                connection.execute("UPDATE research_plans SET holdout_used=1 WHERE plan_id=?", (plan_id,))

    def validate(self, plan_id: str, stage: str, since: int, until: int) -> None:
        with closing(self._connect()) as connection:
            self.validate_on_connection(connection, plan_id, stage, since, until)
