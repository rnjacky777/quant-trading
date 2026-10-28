"""Completed-bar confirmation state for trailing-exit reentry."""
from dataclasses import dataclass

from app.data.models import Candle
from app.risk.regime import slow_slope_multiplier
from app.strategies.base import Action


@dataclass
class PullbackReentry:
    exit_timestamp_ms: int | None = None
    pullback_seen: bool = False

    def reset(self) -> None:
        self.exit_timestamp_ms = None
        self.pullback_seen = False

    def arm(self, timestamp_ms: int) -> None:
        self.exit_timestamp_ms = timestamp_ms
        self.pullback_seen = False

    def observe(self, completed: list[Candle], action: Action) -> bool:
        if self.exit_timestamp_ms is None or len(completed) < 186:
            return False
        last = completed[-1]
        if last.timestamp_ms <= self.exit_timestamp_ms:
            return False
        mean = sum(c.close for c in completed[-24:]) / 24
        if last.close < mean:
            self.pullback_seen = True
            return False
        return (self.pullback_seen and last.close > mean and action is Action.BUY
                and slow_slope_multiplier(completed, 180) == 1.0)
