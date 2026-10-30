"""Multi-coin time-series momentum research on daily perpetual bars with portfolio volatility targeting.

Rules are frozen in docs/research/2026-10-30-multi-coin-trend-design.md. Cross-margin simplification:
positions are signed perp quantities against one USDT balance. Research only; not a paper source.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Callable

import numpy as np

from app.backtest.metrics import calculate_metrics
from app.backtest.models import EquityPoint

DAY_MS = 86400000
MAJORS = frozenset({"BTCUSDT", "ETHUSDT"})
PRE_TRADE_FUNDING_MS = 60000  # the 00:00 funding print (calc_time jitter) settles before the open trade


@dataclass(frozen=True)
class TrendConfig:
    lookback_days: int
    fee_bps: float
    slippage_bps: float
    initial_cash: float = 10000
    vol_target: float = .20
    vol_window: int = 60
    coin_cap: float = .30
    gross_cap: float = 2.0
    account_stop: float = .30


def target_weights(closes: dict[str, list[float]], config: TrendConfig) -> dict[str, float]:
    """closes: per symbol, completed daily closes ending the day before the decision (oldest first)."""
    need = max(config.lookback_days, config.vol_window) + 1
    symbols, signs, rets = [], [], []
    for symbol, series in sorted(closes.items()):
        if len(series) < need:
            continue
        momentum = series[-1] / series[-1 - config.lookback_days] - 1
        if momentum == 0:
            continue
        window = np.asarray(series[-config.vol_window - 1:], dtype=float)
        symbols.append(symbol)
        signs.append(1.0 if momentum > 0 else -1.0)
        rets.append(window[1:] / window[:-1] - 1)
    if not symbols:
        return {}
    r = np.vstack(rets)
    vol = r.std(axis=1, ddof=1) * np.sqrt(365)
    raw = np.asarray(signs) / np.where(vol > 0, vol, np.inf)
    cov = np.atleast_2d(np.cov(r, ddof=1)) * 365
    portfolio = float(np.sqrt(max(raw @ cov @ raw, 0)))
    if portfolio <= 0:
        return {}
    w = np.clip(raw * config.vol_target / portfolio, -config.coin_cap, config.coin_cap)
    gross = np.abs(w).sum()
    if gross > config.gross_cap:
        w *= config.gross_cap / gross
    return {s: float(x) for s, x in zip(symbols, w) if x}


def month_key(t: int) -> str:
    return datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m")


def run_multi_trend(bars: dict[str, dict[int, tuple[float, float, float, float]]], funding: dict[str, list[tuple[int, float]]],
                    universe: dict[str, list[str]], config: TrendConfig, start_ms: int, end_ms: int,
                    weights: Callable[[dict[str, list[float]], TrendConfig, int], dict[str, float]] | None = None) -> dict:
    """weights(closes, config, decision_ms) replaces the time-series direction rule when given."""
    days = range(start_ms, end_ms, DAY_MS)
    cash = config.initial_cash
    qty: dict[str, float] = {}
    last_close: dict[str, float] = {}
    curve = [EquityPoint(start_ms - DAY_MS, config.initial_cash, False)]
    fees = slippage = funding_paid = 0.0
    worst_intraday = 0.0
    stopped_at = None
    log = dict(data_exits=[], rebalances=0)
    by_day: dict[str, dict[int, list[tuple[int, float]]]] = {}
    for symbol, events in funding.items():
        for when, rate in events:
            by_day.setdefault(symbol, {}).setdefault(when // DAY_MS * DAY_MS, []).append((when, rate))

    def slip(symbol: str) -> float:
        return config.slippage_bps * (1 if symbol in MAJORS else 2) / 10000

    def trade(symbol: str, change: float, price: float, extra_slip: float = 1.0) -> None:
        nonlocal cash, fees, slippage
        if not change:
            return
        s = slip(symbol) * extra_slip
        fill = price * (1 + s if change > 0 else 1 - s)
        fee = abs(change) * fill * config.fee_bps / 10000
        cash -= change * fill + fee
        fees += fee
        slippage += abs(change) * price * s
        qty[symbol] = qty.get(symbol, 0.0) + change
        if abs(qty[symbol]) < 1e-12:
            del qty[symbol]

    def pay_funding(t: int, pre_trade: bool) -> None:
        nonlocal cash, funding_paid
        for symbol, q in list(qty.items()):
            for when, rate in by_day.get(symbol, {}).get(t, []):
                if (when - t <= PRE_TRADE_FUNDING_MS) == pre_trade:
                    amount = q * bars[symbol][t][0] * rate
                    cash -= amount
                    funding_paid += amount

    for t in days:
        last = t == days[-1]
        for symbol in [s for s in qty if t not in bars.get(s, {})]:
            trade(symbol, -qty[symbol], last_close[symbol], extra_slip=2.0)
            log["data_exits"].append(dict(timestamp_ms=t, symbol=symbol))
        if stopped_at is None:
            pay_funding(t, pre_trade=True)
            members = set(universe.get(month_key(t), []))
            weekday = datetime.fromtimestamp(t / 1000, timezone.utc).weekday()
            if (t == start_ms or weekday == 0) and not last:
                equity = cash + sum(q * bars[s][t][0] for s, q in qty.items())
                need = max(config.lookback_days, config.vol_window) + 1
                closes = {}
                for symbol in members:
                    series = [bars.get(symbol, {}).get(t - k * DAY_MS) for k in range(need, 0, -1)]
                    if all(series) and t in bars.get(symbol, {}):
                        closes[symbol] = [b[3] for b in series]
                targets = weights(closes, config, t) if weights else target_weights(closes, config)
                for symbol in sorted(set(qty) | set(targets)):
                    target = targets.get(symbol, 0.0) * equity / bars[symbol][t][0]
                    trade(symbol, target - qty.get(symbol, 0.0), bars[symbol][t][0])
                log["rebalances"] += 1
            elif datetime.fromtimestamp(t / 1000, timezone.utc).day == 1:
                for symbol in [s for s in qty if s not in members]:
                    trade(symbol, -qty[symbol], bars[symbol][t][0])
            pay_funding(t, pre_trade=False)
        adverse = cash + sum(q * (bars[s][t][2] if q > 0 else bars[s][t][1]) for s, q in qty.items())
        worst_intraday = min(worst_intraday, adverse / config.initial_cash - 1)
        equity = cash + sum(q * bars[s][t][3] for s, q in qty.items())
        if stopped_at is None and equity <= config.initial_cash * (1 - config.account_stop):
            for symbol in list(qty):
                trade(symbol, -qty[symbol], bars[symbol][t][3])
            stopped_at = t
        if last:
            for symbol in list(qty):
                trade(symbol, -qty[symbol], bars[symbol][t][3])
        for symbol in qty:
            last_close[symbol] = bars[symbol][t][3]
        equity = cash + sum(q * bars[s][t][3] for s, q in qty.items())
        if not isfinite(equity) or equity <= 0:
            raise ValueError("trend account insolvent")
        curve.append(EquityPoint(t, equity, bool(qty)))
    if qty or abs(cash - curve[-1].equity) > 1e-6:
        raise ValueError("trend account does not reconcile after exit")
    metrics = calculate_metrics(curve, [], config.initial_cash, "1d")
    return dict(metrics=asdict(metrics), final_equity=cash, fees=fees, slippage=slippage, funding_paid=funding_paid,
                worst_intraday_from_start=worst_intraday, account_stop_at_ms=stopped_at,
                invested_days=sum(p.invested for p in curve), **log)
