"""Append-only, hash-chained JSONL event ledger for paper runs.

Events are never rewritten. A stable event_id makes appends idempotent, so a
restarted runner cannot record the same decision or fill twice.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path

GENESIS = "0" * 64


def _digest(record: dict) -> str:
    body = {k: record[k] for k in ("seq", "type", "event_id", "recorded_ms", "payload", "prev")}
    return sha256(json.dumps(body, sort_keys=True, allow_nan=False, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class LedgerEvent:
    seq: int
    type: str
    event_id: str
    recorded_ms: int
    payload: dict


class LedgerCorrupted(ValueError):
    pass


class PaperLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.events: list[LedgerEvent] = []
        self._ids: set[str] = set()
        self._last = GENESIS
        if path.exists():
            self._load()

    def _load(self) -> None:
        raw = self.path.read_bytes()
        if raw and not raw.endswith(b"\n"):
            raise LedgerCorrupted("ledger ends with a partial record; investigate before restarting")
        for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            record = json.loads(line)
            if record["seq"] != len(self.events) + 1 or record["prev"] != self._last or _digest(record) != record["hash"]:
                raise LedgerCorrupted(f"ledger chain broken at line {number}")
            if record["event_id"] in self._ids:
                raise LedgerCorrupted(f"duplicate event_id at line {number}")
            self._ids.add(record["event_id"])
            self._last = record["hash"]
            self.events.append(LedgerEvent(record["seq"], record["type"], record["event_id"],
                                           record["recorded_ms"], record["payload"]))

    def __contains__(self, event_id: str) -> bool:
        return event_id in self._ids

    def append(self, type_: str, event_id: str, payload: dict, recorded_ms: int) -> LedgerEvent | None:
        """Durably append; returns None when the event_id was already recorded."""
        if event_id in self._ids:
            return None
        record = dict(seq=len(self.events) + 1, type=type_, event_id=event_id, recorded_ms=recorded_ms,
                      payload=payload, prev=self._last)
        record["hash"] = _digest(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, allow_nan=False, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._ids.add(event_id)
        self._last = record["hash"]
        event = LedgerEvent(record["seq"], type_, event_id, recorded_ms, payload)
        self.events.append(event)
        return event
