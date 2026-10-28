from collections.abc import Sequence
from math import isfinite

from app.data.models import Candle
from app.data.aggregation import completed_four_hour_bars


def directional_slope_cap(candles: list[Candle], direction: int) -> float:
    """Cap risk at half when completed 4h SMA60 slope over 24h conflicts.

    This is a conservative budget cap, never a win probability or leverage score.
    """
    if direction not in (-1, 1):
        raise ValueError("direction must be long or short")
    bars=completed_four_hour_bars(candles,count=66)
    if len(bars)<66:
        return .5
    movement=sum(c.close for c in bars[-60:])-sum(c.close for c in bars[-66:-6])
    return 1. if direction*movement>0 else .5


def loss_streak_multiplier(closed_pnls: Sequence[float]) -> float:
    """Halve budget after two losses until a profit; zero PnL does not reset.

    Realized outcomes are a risk brake, not a forecast or calibrated confidence.
    """
    losses = 0
    for pnl in reversed(closed_pnls):
        if not isfinite(pnl):
            raise ValueError("closed PnL must be finite")
        if pnl > 0:
            break
        if pnl < 0:
            losses += 1
        if losses >= 2:
            return .5
    return 1.0


def directional_loss_guard_multiplier(shared_pnls: Sequence[float], directional_pnls: Sequence[float]) -> float:
    """Retain shared loss protection; opposite-side wins cannot unlock own losses."""
    return min(loss_streak_multiplier(shared_pnls),loss_streak_multiplier(directional_pnls))


def slow_slope_multiplier(candles: Sequence[Candle], period: int, lag: int = 6) -> float:
    """Completed-bar SMA slope; insufficient history gets reduced risk.

    Positive slope gets the existing budget, flat/down gets half. This never
    increases the configured maximum budget or predicts an individual winner.
    """
    if period < 2 or lag < 1:
        raise ValueError("invalid slope windows")
    if len(candles) < period + lag:
        return 0.5
    current = sum(c.close for c in candles[-period:]) / period
    previous = sum(c.close for c in candles[-period-lag:-lag]) / period
    return 1.0 if current > previous else 0.5
