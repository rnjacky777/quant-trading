from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 10_000.0
    fee_bps: float = 10.0
    slippage_bps: float = 5.0
    position_fraction: float = 1.0
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    leverage: float = 1.0
    liquidation_fee_bps: float = 0.0
    market_type: str = "spot"

    def __post_init__(self) -> None:
        if not isfinite(self.initial_cash) or self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if not isfinite(self.fee_bps) or not isfinite(self.slippage_bps):
            raise ValueError("costs must be finite")
        if self.fee_bps < 0 or self.slippage_bps < 0:
            raise ValueError("costs must be non-negative")
        if not isfinite(self.position_fraction) or not 0 < self.position_fraction <= 1:
            raise ValueError("position_fraction must be in (0, 1]")
        for name, value in (
            ("stop_loss_pct", self.stop_loss_pct),
            ("take_profit_pct", self.take_profit_pct),
        ):
            if value is not None and (not isfinite(value) or not 0 < value < 1):
                raise ValueError(f"{name} must be in (0, 1) or None")
        if not isfinite(self.leverage) or not 1 <= self.leverage <= 10:
            raise ValueError("leverage must be between 1 and 10")
        if not isfinite(self.liquidation_fee_bps) or self.liquidation_fee_bps < 0:
            raise ValueError("liquidation_fee_bps must be finite and non-negative")
        if self.market_type not in {"spot", "perpetual"}:
            raise ValueError("market_type must be spot or perpetual")


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
    exit_reason: str
    stop_loss_price: float | None
    take_profit_price: float | None
    leverage: float
    funding: float = 0.0
    liquidation_fee: float = 0.0


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
    net_funding: float
    liquidation_fees: float
    liquidation_count: int
    maximum_margin_ratio: float


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
