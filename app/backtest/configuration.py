import json

from app.backtest.models import BacktestConfig
from app.strategies.base import Strategy
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from app.strategies.mean_reversion import MeanReversionStrategy
from app.strategies.momentum import MomentumStrategy
from app.strategies.protection import FixedPercentageProtection
from app.strategies.trend_following import MovingAverageTrendStrategy
from app.strategies.multitimeframe import CompletedFourHourTrend
from app.strategies.intraday import IntradayTrendStrategy


def strategy_family(name: str) -> str:
    if name.startswith("intraday_"):
        return "intraday"
    if name.startswith("sma_"):
        return "sma"
    if name.startswith("momentum_"):
        return "momentum"
    if name.startswith("mean_reversion_"):
        return "mean-reversion"
    if name == "buy_and_hold":
        return "buy-hold"
    raise ValueError(f"unsupported saved strategy: {name}")


def make_strategy(
    family: str, config: BacktestConfig, *, fast: int = 20, slow: int = 60,
    lookback: int = 20, momentum_threshold: float = 0, entry_deviation: float = 0.05,
) -> Strategy:
    strategy: Strategy
    if config.higher_timeframe_filter and family != "sma":
        raise ValueError("4h trend filter currently supports hourly SMA only")
    if config.trailing_reentry_mode == "pullback_reclaim" and family != "sma":
        raise ValueError("pullback reclaim applies only to SMA")
    if config.risk_regime == "slow_slope" and family != "sma":
        raise ValueError("slow-slope risk sizing requires SMA")
    if family != "sma" and config.trend_entry_buffer:
        raise ValueError("trend entry buffer applies only to SMA")
    if family == "sma":
        strategy = MovingAverageTrendStrategy(fast, slow, config.trend_entry_buffer)
    elif family == "intraday":
        if config.risk_per_trade is None or config.exit_mode != "signal":
            raise ValueError("intraday requires a risk budget and signal exits")
        strategy = IntradayTrendStrategy(config.intraday_entry, config.intraday_min_atr_fraction, config.intraday_strong_close)
    elif family == "momentum":
        strategy = MomentumStrategy(lookback, momentum_threshold)
    elif family == "mean-reversion":
        strategy = MeanReversionStrategy(lookback, entry_deviation)
    elif family == "buy-hold":
        strategy = BuyAndHoldStrategy()
    else:
        raise ValueError("unsupported strategy")
    if config.higher_timeframe_filter:
        strategy = CompletedFourHourTrend(strategy)
    if config.risk_per_trade is not None and family != "intraday":
        strategy = FixedPercentageProtection(strategy, config.stop_loss_pct)
    return strategy


def saved_policy(config: BacktestConfig, strategy_name: str) -> str:
    policy: dict[str, object] = {}
    for key in ("max_entries_per_day", "max_holding_bars"):
        if getattr(config, key) is not None:
            policy[key] = getattr(config, key)
    if strategy_family(strategy_name) == "intraday":
        policy["intraday_entry"] = config.intraday_entry
        if config.intraday_min_atr_fraction:
            policy["intraday_min_atr_fraction"] = config.intraday_min_atr_fraction
        if config.intraday_strong_close:
            policy["intraday_strong_close"] = True
    if config.higher_timeframe_filter:
        policy["higher_timeframe_filter"] = True
    if config.risk_regime != "fixed":
        policy["risk_regime"] = config.risk_regime
    if config.risk_per_trade is not None or config.max_exposure_fraction != 1 or config.exit_mode != "fixed" or config.position_fraction != 1:
        policy.update(
            risk_per_trade=float(config.risk_per_trade) if config.risk_per_trade is not None else None,
            max_exposure_fraction=float(config.max_exposure_fraction),
            exit_mode=config.exit_mode,
            position_fraction=float(config.position_fraction),
        )
    if config.trailing_reentry_mode != "inherit":
        policy["trailing_reentry_mode"] = config.trailing_reentry_mode
    if config.trailing_activation is not None:
        policy.update(trailing_activation=config.trailing_activation, trailing_distance=config.trailing_distance)
    if config.trend_entry_buffer:
        policy["trend_entry_buffer"] = config.trend_entry_buffer
    if config.stop_reentry_mode != "immediate":
        policy["stop_reentry_mode"] = config.stop_reentry_mode
    if strategy_family(strategy_name) in {"momentum", "mean-reversion"}:
        policy["strategy_name"] = strategy_name
    return json.dumps(policy, sort_keys=True, separators=(",", ":"))
