from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 10_000.0
    fee_bps: float = 10.0
    slippage_bps: float = 5.0
    position_fraction: float = 1.0

    def __post_init__(self) -> None:
        if not isfinite(self.initial_cash) or self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if not isfinite(self.fee_bps) or not isfinite(self.slippage_bps):
            raise ValueError("costs must be finite")
        if self.fee_bps < 0 or self.slippage_bps < 0:
            raise ValueError("costs must be non-negative")
        if not isfinite(self.position_fraction) or not 0 < self.position_fraction <= 1:
            raise ValueError("position_fraction must be in (0, 1]")


@dataclass(frozen=True)
class Trade:
    entry_timestamp_ms: int
    exit_timestamp_ms: int
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    return_pct: float
    fees: float
    slippage_cost: float


@dataclass(frozen=True)
class EquityPoint:
    timestamp_ms: int
    equity: float
    invested: bool


@dataclass(frozen=True)
class PerformanceMetrics:
    total_return: float
    cagr: float
    sharpe_ratio: float
    sortino_ratio: float
    maximum_drawdown: float
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    number_of_trades: int
    exposure: float
    fees: float
    slippage: float


@dataclass(frozen=True)
class BacktestResult:
    strategy_name: str
    symbol: str
    timeframe: str
    initial_cash: float
    final_equity: float
    metrics: PerformanceMetrics
    trades: list[Trade]
    equity_curve: list[EquityPoint]
