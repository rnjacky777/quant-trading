import json
from pathlib import Path

from app.backtest.configuration import make_strategy, strategy_family
from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig, BacktestResult
from app.backtest.runs import BacktestRun, BacktestRunRepository, _fingerprint
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository
from app.strategies.base import Strategy


def config_for_run(run: BacktestRun) -> BacktestConfig:
    policy = json.loads(run.policy_json)
    return BacktestConfig(
        initial_cash=run.initial_cash, fee_bps=run.fee_bps, slippage_bps=run.slippage_bps,
        stop_loss_pct=run.stop_loss_pct, take_profit_pct=run.take_profit_pct,
        leverage=run.leverage,
        **{key: policy[key] for key in ("intraday_strong_close", "intraday_min_atr_fraction", "intraday_entry", "max_entries_per_day", "max_holding_bars", "higher_timeframe_filter", "risk_regime", "risk_per_trade", "max_exposure_fraction", "exit_mode", "position_fraction", "stop_reentry_mode", "trend_entry_buffer", "trailing_activation", "trailing_distance", "trailing_reentry_mode") if key in policy},
    )


def strategy_for_run(
    run: BacktestRun, config: BacktestConfig, fast: int | None = None, slow: int | None = None,
    **overrides: int | float,
) -> Strategy:
    family = strategy_family(run.strategy_name)
    params: dict[str, int | float] = {}
    if family == "momentum":
        _, lookback, threshold = run.strategy_name.split("_")
        params.update(lookback=int(lookback), momentum_threshold=float(threshold))
    elif family == "mean-reversion":
        _, _, lookback, deviation = run.strategy_name.split("_")
        params.update(lookback=int(lookback), entry_deviation=float(deviation))
    params.update(overrides)
    return make_strategy(family, config, fast=fast or run.fast_period or 20,
                         slow=slow or run.slow_period or 60, **params)


def reproduce_run(
    db_path: Path, exchange: str, run: BacktestRun,
) -> tuple[list[Candle], list[Candle], BacktestResult, BacktestConfig]:
    repository = CandleRepository(db_path)
    candles = repository.list_range(exchange, run.symbol, run.timeframe, run.since_ms,
                                    run.until_ms + TIMEFRAMES_MS[run.timeframe])
    if not candles:
        raise ValueError("selected backtest candles are unavailable")
    signal_candles = candles
    start = None
    if _fingerprint(candles) != run.data_fingerprint:
        family = strategy_family(run.strategy_name)
        warmup = run.slow_period or 1
        if family == "momentum":
            warmup = int(run.strategy_name.split("_")[1]) + 1
        elif family == "mean-reversion":
            warmup = int(run.strategy_name.split("_")[2])
        if config_for_run(run).risk_regime == "slow_slope" or config_for_run(run).trailing_reentry_mode == "pullback_reclaim":
            warmup = max(warmup, 186)
        if family == "intraday":
            warmup = max(warmup, 243)
        if config_for_run(run).higher_timeframe_filter:
            warmup = max(warmup, 243)
        # Optimized runs may retain their parent's exact signal dataset.
        # Accept an ancestral warmup only when its entire fingerprint matches.
        warmups = [warmup]
        versions = BacktestRunRepository(db_path)
        version = versions.get_strategy_version(run.strategy_key)
        visited: set[str] = set()
        while version is not None and version.strategy_key not in visited:
            visited.add(version.strategy_key)
            if version.slow_period is not None:
                warmups.append(version.slow_period)
            version = versions.get_strategy_version(version.previous_strategy_key) if version.previous_strategy_key else None
        for count in dict.fromkeys(warmups):
            warmup_since = max(0, run.since_ms - count * TIMEFRAMES_MS[run.timeframe])
            before = repository.list_range(exchange, run.symbol, run.timeframe, warmup_since, run.since_ms) if warmup_since < run.since_ms else []
            candidate = before + candles
            if _fingerprint(candidate) == run.data_fingerprint:
                signal_candles = candidate
                start = run.since_ms
                break
    if _fingerprint(signal_candles) != run.data_fingerprint:
        raise ValueError("selected backtest dataset changed; exact reproduction is unavailable")
    config = config_for_run(run)
    result = BacktestEngine(config).run(signal_candles, strategy_for_run(run, config), evaluation_start_ms=start)
    return candles, signal_candles, result, config
