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
    risk_per_trade: float | None = None
    max_exposure_fraction: float = 1.0
    exit_mode: str = "fixed"
    stop_reentry_mode: str = "immediate"
    trend_entry_buffer: float = 0.0
    trailing_activation: float | None = None
    trailing_distance: float | None = None
    trailing_reentry_mode: str = "inherit"
    risk_regime: str = "fixed"
    higher_timeframe_filter: bool = False
    intraday_entry: str = "breakout"
    intraday_min_atr_fraction: float = 0.0
    intraday_strong_close: bool = False
    max_entries_per_day: int | None = None
    max_holding_bars: int | None = None

    def __post_init__(self) -> None:
        if type(self.intraday_strong_close) is not bool:
            raise ValueError("intraday_strong_close must be boolean")
        if not isfinite(self.intraday_min_atr_fraction) or not 0 <= self.intraday_min_atr_fraction < 1:
            raise ValueError("invalid intraday minimum ATR")
        if self.intraday_entry not in {"breakout", "pullback"}:
            raise ValueError("invalid intraday_entry")
        for value in (self.max_entries_per_day, self.max_holding_bars):
            if value is not None and (type(value) is not int or value < 1):
                raise ValueError("entry and holding limits must be positive integers")
        if type(self.higher_timeframe_filter) is not bool:
            raise ValueError("higher_timeframe_filter must be boolean")
        if self.risk_regime not in {"fixed", "slow_slope", "loss_streak"}:
            raise ValueError("invalid risk_regime")
        if self.risk_regime != "fixed" and self.risk_per_trade is None:
            raise ValueError("regime sizing requires a risk budget")
        if self.trailing_reentry_mode not in {"inherit", "exit_high_breakout", "pullback_reclaim"}:
            raise ValueError("invalid trailing_reentry_mode")
        if self.trailing_reentry_mode != "inherit" and self.trailing_activation is None:
            raise ValueError("trailing breakout reentry requires an enabled trailing stop")
        if (self.trailing_activation is None) != (self.trailing_distance is None):
            raise ValueError("trailing activation and distance must be configured together")
        for value in (self.trailing_activation, self.trailing_distance):
            if value is not None and (not isfinite(value) or not 0 < value < 1):
                raise ValueError("trailing percentages must be in (0, 1)")
        if self.trailing_activation is not None and (self.stop_loss_pct is None or (self.market_type == "spot" and self.leverage != 1)):
            raise ValueError("trailing stop requires an initial stop and unlevered spot or validated perpetual inputs")
        if not isfinite(self.trend_entry_buffer) or not 0 <= self.trend_entry_buffer < 1:
            raise ValueError("trend_entry_buffer must be in [0, 1)")
        if self.stop_reentry_mode not in {"immediate", "signal_reset"}:
            raise ValueError("stop_reentry_mode must be immediate or signal_reset")
        if self.exit_mode not in {"fixed", "signal"}:
            raise ValueError("exit_mode must be fixed or signal")
        if not isfinite(self.max_exposure_fraction) or not 0 < self.max_exposure_fraction <= 1:
            raise ValueError("max_exposure_fraction must be in (0, 1]")
        if self.risk_per_trade is not None:
            if not isfinite(self.risk_per_trade) or not 0 < self.risk_per_trade <= 1:
                raise ValueError("risk_per_trade must be in (0, 1]")
            if self.leverage != 1 or self.market_type != "spot":
                raise ValueError("risk-budget sizing currently requires unlevered spot mode")
            if self.stop_loss_pct is None:
                raise ValueError("risk-budget sizing requires a protective stop")
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
    planned_risk: float = 0.0


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
