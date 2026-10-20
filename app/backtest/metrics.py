from math import inf, sqrt

import numpy as np

from app.backtest.models import EquityPoint, PerformanceMetrics, Trade
from app.data.models import TIMEFRAMES_MS


def calculate_metrics(
    equity_curve: list[EquityPoint],
    trades: list[Trade],
    initial_cash: float,
    timeframe: str,
) -> PerformanceMetrics:
    if not equity_curve:
        raise ValueError("equity curve cannot be empty")
    values = np.asarray([point.equity for point in equity_curve], dtype=float)
    returns = values[1:] / values[:-1] - 1 if len(values) > 1 else np.asarray([])
    periods_per_year = 365.25 * 24 * 60 * 60 * 1000 / TIMEFRAMES_MS[timeframe]
    sharpe = _ratio(returns, returns.std(ddof=1) if len(returns) > 1 else 0.0, periods_per_year)
    downside_deviation = (
        float(np.sqrt(np.mean(np.minimum(returns, 0.0) ** 2)))
        if len(returns) else 0.0
    )
    sortino = _ratio(returns, downside_deviation, periods_per_year)

    peaks = np.maximum.accumulate(values)
    max_drawdown = float(np.min(values / peaks - 1))
    elapsed_years = (
        (equity_curve[-1].timestamp_ms - equity_curve[0].timestamp_ms)
        / (365.25 * 24 * 60 * 60 * 1000)
    )
    total_return = float(values[-1] / initial_cash - 1)
    cagr = (values[-1] / initial_cash) ** (1 / elapsed_years) - 1 if elapsed_years > 0 else 0.0
    wins = [trade.pnl for trade in trades if trade.pnl > 0]
    losses = [trade.pnl for trade in trades if trade.pnl < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss else (inf if gross_profit else 0.0)

    return PerformanceMetrics(
        total_return=total_return,
        cagr=float(cagr),
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        maximum_drawdown=max_drawdown,
        win_rate=len(wins) / len(trades) if trades else 0.0,
        profit_factor=profit_factor,
        average_win=sum(wins) / len(wins) if wins else 0.0,
        average_loss=sum(losses) / len(losses) if losses else 0.0,
        number_of_trades=len(trades),
        exposure=sum(point.invested for point in equity_curve) / len(equity_curve),
        fees=sum(trade.fees for trade in trades),
        slippage=sum(trade.slippage_cost for trade in trades),
    )


def _ratio(returns: np.ndarray, deviation: float, periods_per_year: float) -> float:
    if len(returns) == 0 or deviation <= 0:
        return 0.0
    return float(returns.mean() / deviation * sqrt(periods_per_year))
