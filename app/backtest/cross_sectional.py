"""Cross-sectional crypto momentum research (design: docs/research/2026-10-30-cross-sectional-momentum-design.md).

Only the direction rule differs from the multi-coin trend engine: rank the universe by L-day return,
long the top N and short the bottom N, then apply the same inverse-vol, covariance vol-target and caps.
"""
from typing import Callable

import numpy as np

from app.backtest import multi_trend
from app.backtest.multi_trend import TrendConfig

LEGS = 4


def cross_sectional_weights(closes: dict[str, list[float]], config: TrendConfig) -> dict[str, float]:
    need = max(config.lookback_days, config.vol_window) + 1
    ready = {s: c for s, c in closes.items() if len(c) >= need}
    if len(ready) < 2 * LEGS:
        return {}
    momentum = {s: c[-1] / c[-1 - config.lookback_days] - 1 for s, c in ready.items()}
    ranked = sorted(ready, key=lambda s: (momentum[s], s))
    sides = {s: -1.0 for s in ranked[:LEGS]} | {s: 1.0 for s in ranked[-LEGS:]}
    symbols = sorted(sides)
    rets = np.vstack([np.diff(np.asarray(ready[s][-config.vol_window - 1:])) / np.asarray(ready[s][-config.vol_window - 1:-1])
                      for s in symbols])
    vol = rets.std(axis=1, ddof=1) * np.sqrt(365)
    raw = np.asarray([sides[s] for s in symbols]) / np.where(vol > 0, vol, np.inf)
    portfolio = float(np.sqrt(max(raw @ (np.cov(rets, ddof=1) * 365) @ raw, 0)))
    if portfolio <= 0:
        return {}
    w = np.clip(raw * config.vol_target / portfolio, -config.coin_cap, config.coin_cap)
    gross = np.abs(w).sum()
    if gross > config.gross_cap:
        w *= config.gross_cap / gross
    return {s: float(x) for s, x in zip(symbols, w) if x}


def run_cross_sectional(*args, **kwargs) -> dict:
    """Run the multi-coin engine with the cross-sectional direction rule swapped in."""
    original = multi_trend.target_weights
    multi_trend.target_weights = cross_sectional_weights
    try:
        return multi_trend.run_multi_trend(*args, **kwargs)
    finally:
        multi_trend.target_weights = original


def funding_weights(funding: dict[str, list[tuple[int, float]]]) -> Callable:
    """Short the highest and long the lowest mean funding published in the past L days (design: cross-sectional funding)."""
    def rule(closes: dict[str, list[float]], config: TrendConfig, decision_ms: int) -> dict[str, float]:
        need = max(config.lookback_days, config.vol_window) + 1
        window = config.lookback_days * multi_trend.DAY_MS
        mean = {}
        for symbol, series in closes.items():
            rates = [r for when, r in funding.get(symbol, []) if decision_ms - window <= when < decision_ms]
            if len(series) >= need and rates:
                mean[symbol] = sum(rates) / len(rates)
        if len(mean) < 2 * LEGS:
            return {}
        ranked = sorted(mean, key=lambda s: (mean[s], s))
        sides = {s: 1.0 for s in ranked[:LEGS]} | {s: -1.0 for s in ranked[-LEGS:]}
        return scale(sides, closes, config)
    return rule


def scale(sides: dict[str, float], closes: dict[str, list[float]], config: TrendConfig) -> dict[str, float]:
    """Inverse-vol raw weights, covariance vol target, then coin and gross caps."""
    symbols = sorted(sides)
    rets = np.vstack([np.diff(np.asarray(closes[s][-config.vol_window - 1:])) / np.asarray(closes[s][-config.vol_window - 1:-1])
                      for s in symbols])
    vol = rets.std(axis=1, ddof=1) * np.sqrt(365)
    raw = np.asarray([sides[s] for s in symbols]) / np.where(vol > 0, vol, np.inf)
    portfolio = float(np.sqrt(max(raw @ (np.cov(rets, ddof=1) * 365) @ raw, 0)))
    if portfolio <= 0:
        return {}
    w = np.clip(raw * config.vol_target / portfolio, -config.coin_cap, config.coin_cap)
    gross = np.abs(w).sum()
    if gross > config.gross_cap:
        w *= config.gross_cap / gross
    return {s: float(x) for s, x in zip(symbols, w) if x}
