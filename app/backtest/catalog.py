"""Editable research organization, separate from immutable strategy versions."""
from contextlib import closing
from pathlib import Path
import sqlite3
from time import time

from app.backtest.runs import StrategyVersion


CATEGORY_LABELS = {
    "focus": "主要研究",
    "reference": "對照基準",
    "candidate": "待評估",
    "archived": "已封存",
}
CATEGORY_ORDER = {key: index for index, key in enumerate(CATEGORY_LABELS)}


class VersionCatalogRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("""CREATE TABLE IF NOT EXISTS strategy_version_catalog (
            strategy_key TEXT PRIMARY KEY,
            category TEXT NOT NULL CHECK(category IN ('focus','reference','candidate','archived')),
            updated_at_ms INTEGER NOT NULL
        )""")
        return connection

    def categories(self, versions: list[StrategyVersion]) -> dict[str, str]:
        with closing(self._connect()) as connection:
            stored = {row["strategy_key"]: row["category"] for row in connection.execute(
                "SELECT strategy_key,category FROM strategy_version_catalog"
            )}
        # New experiments stay candidates. Original baseline versions stay references.
        return {version.strategy_key: stored.get(
            version.strategy_key, "reference" if version.previous_strategy_key is None else "candidate"
        ) for version in versions}

    def set_category(self, strategy_key: str, category: str) -> None:
        if category not in CATEGORY_LABELS:
            raise ValueError("策略分類無效")
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            version = connection.execute("SELECT * FROM strategy_versions WHERE strategy_key=?", (strategy_key,)).fetchone()
            if version is None:
                raise ValueError("找不到策略版本")
            if category == "focus":
                # A series has one focus; its former focus remains available as a reference.
                connection.execute("""UPDATE strategy_version_catalog SET category='reference',updated_at_ms=?
                    WHERE category='focus' AND strategy_key<>? AND strategy_key IN (
                        SELECT strategy_key FROM strategy_versions
                        WHERE strategy_family=? AND symbol=? AND timeframe=?
                    )""", (int(time()*1000), strategy_key, version["strategy_family"], version["symbol"], version["timeframe"]))
            connection.execute("""INSERT INTO strategy_version_catalog VALUES(?,?,?)
                ON CONFLICT(strategy_key) DO UPDATE SET category=excluded.category,updated_at_ms=excluded.updated_at_ms""",
                               (strategy_key, category, int(time()*1000)))


def group_versions(items: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str, str], dict] = {}
    for item in items:
        version = item["version"]
        key = (version.strategy_family, version.symbol, version.timeframe)
        group = groups.setdefault(key, dict(
            label=item["strategy_label"], symbol=version.symbol, timeframe=version.timeframe,
            primary=[], candidate=[], archived=[], count=0, experiment_count=0,
        ))
        section = "primary" if item["category"] in {"focus", "reference"} else item["category"]
        group[section].append(item)
        group["count"] += 1
        group["experiment_count"] += item["experiment_count"]
    for group in groups.values():
        for section in ("candidate", "archived"):
            group[section + "_pending"] = any(item.get("optimization_request") and item["optimization_request"].status == "pending" for item in group[section])
        for section in ("primary", "candidate", "archived"):
            group[section].sort(key=lambda item: (
                CATEGORY_ORDER[item["category"]], -item["version"].version_number
            ))
    return list(groups.values())
