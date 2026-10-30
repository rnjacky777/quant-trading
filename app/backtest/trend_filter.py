"""BTC spot long-term moving-average filter research (design: docs/research/2026-10-30-btc-trend-filter-design.md).

Long-only, unlevered spot: hold BTC while the previous close is above its N-day mean, otherwise USDT.
"""
from dataclasses import asdict, dataclass
from math import isfinite

from app.backtest.metrics import calculate_metrics
from app.backtest.models import EquityPoint

DAY_MS = 86400000


@dataclass(frozen=True)
class FilterConfig:
    window_days: int
    fee_bps: float
    slippage_bps: float
    initial_cash: float = 10000
    account_stop: float = .30


def wants_btc(closes: list[float], window: int) -> bool:
    """closes end with the previous completed day; False until the window has enough history."""
    return len(closes) >= window and closes[-1] > sum(closes[-window:]) / window


def run_trend_filter(bars: dict[int, tuple[float, float, float, float]], config: FilterConfig,
                     start_ms: int, end_ms: int) -> dict:
    days = range(start_ms, end_ms, DAY_MS)
    history = [bars[t][3] for t in sorted(bars) if t < start_ms]
    cash, btc = config.initial_cash, 0.0
    fees = slippage = 0.0
    switches = 0
    stopped_at = None
    curve = [EquityPoint(start_ms - DAY_MS, config.initial_cash, False)]

    def trade(quantity: float, price: float) -> None:
        nonlocal cash, btc, fees, slippage, switches
        s = config.slippage_bps / 10000
        fill = price * (1 + s if quantity > 0 else 1 - s)
        fee = abs(quantity) * fill * config.fee_bps / 10000
        cash -= quantity * fill + fee
        btc += quantity
        fees += fee
        slippage += abs(quantity) * price * s
        switches += 1

    for t in days:
        o, _, _, c = bars[t]
        if stopped_at is None and t != days[-1]:
            hold = wants_btc(history, config.window_days)
            if hold and not btc:
                trade(cash / (o * (1 + config.slippage_bps / 10000) * (1 + config.fee_bps / 10000)), o)
            elif not hold and btc:
                trade(-btc, o)
        equity = cash + btc * c
        if stopped_at is None and btc and equity <= config.initial_cash * (1 - config.account_stop):
            trade(-btc, c)
            stopped_at = t
        if t == days[-1] and btc:
            trade(-btc, c)
        equity = cash + btc * c
        if not isfinite(equity) or equity <= 0:
            raise ValueError("filter account insolvent")
        curve.append(EquityPoint(t, equity, btc > 0))
        history.append(c)
    if btc or abs(cash - curve[-1].equity) > 1e-6:
        raise ValueError("filter account does not reconcile after exit")
    metrics = calculate_metrics(curve, [], config.initial_cash, "1d")
    return dict(metrics=asdict(metrics), final_equity=cash, fees=fees, slippage=slippage, trades=switches,
                account_stop_at_ms=stopped_at, invested_days=sum(p.invested for p in curve))
