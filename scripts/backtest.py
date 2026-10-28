import argparse
from dataclasses import asdict
from datetime import datetime
import json
from math import isfinite

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.backtest.configuration import make_strategy
from app.backtest.runs import BacktestRunRepository
from app.backtest.research import ResearchPlanRepository
from app.config.settings import Settings
from app.data.models import TIMEFRAMES_MS
from app.data.repository import CandleRepository


def utc_milliseconds(value: str) -> int:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("timestamp needs a UTC offset")
    return int(parsed.timestamp() * 1000)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a long/cash baseline backtest")
    parser.add_argument("--symbol", choices=["BTC/USDT", "ETH/USDT"], required=True)
    parser.add_argument("--timeframe", choices=["1h", "4h", "1d"], required=True)
    parser.add_argument("--since", type=utc_milliseconds, required=True)
    parser.add_argument("--until", type=utc_milliseconds, required=True)
    parser.add_argument("--strategy", choices=["sma", "buy-hold", "momentum", "mean-reversion", "intraday"], default="sma")
    parser.add_argument("--intraday-strong-close", action="store_true")
    parser.add_argument("--intraday-min-atr-pct", type=float, default=0)
    parser.add_argument("--intraday-entry", choices=["breakout", "pullback"], default="breakout")
    parser.add_argument("--max-entries-per-day", type=int, default=0)
    parser.add_argument("--max-holding-bars", type=int, default=0)
    parser.add_argument("--lookback", type=int, default=20)
    parser.add_argument("--momentum-threshold", type=float, default=0.0)
    parser.add_argument("--entry-deviation", type=float, default=0.05)
    parser.add_argument("--trailing-reentry-mode", choices=["inherit", "exit_high_breakout"], default="inherit")
    parser.add_argument("--trailing-activation-pct", type=float, default=0)
    parser.add_argument("--trailing-distance-pct", type=float, default=0)
    parser.add_argument("--trend-entry-buffer-pct", type=float, default=0)
    parser.add_argument("--fast", type=int, default=20)
    parser.add_argument("--slow", type=int, default=60)
    parser.add_argument("--initial-cash", type=float, default=10_000)
    parser.add_argument("--fee-bps", type=float, default=10)
    parser.add_argument("--slippage-bps", type=float, default=5)
    parser.add_argument("--stop-loss-pct", type=float, default=0)
    parser.add_argument("--take-profit-pct", type=float, default=0)
    parser.add_argument("--leverage", type=float, choices=[1], default=1)
    parser.add_argument("--risk-regime", choices=["fixed", "slow_slope", "loss_streak"], default="fixed")
    parser.add_argument("--risk-per-trade-pct", type=float, default=0)
    parser.add_argument("--max-exposure-pct", type=float, default=100)
    parser.add_argument("--exit-mode", choices=["fixed", "signal"], default="fixed")
    parser.add_argument("--stop-reentry-mode", choices=["immediate", "signal_reset"], default="immediate")
    parser.add_argument("--stage", choices=["development", "validation", "out_of_sample"], default="development")
    parser.add_argument("--research-plan-id", default="")
    parser.add_argument("--base-run-key", default=None)
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    settings = Settings.from_env()
    repository = CandleRepository(settings.db_path)
    if args.research_plan_id:
        ResearchPlanRepository(settings.db_path).validate(args.research_plan_id, args.stage, args.since, args.until)
    elif args.stage == "out_of_sample":
        parser.error("out_of_sample requires a preregistered research plan")
    candles = repository.list_range(
        settings.exchange_id, args.symbol, args.timeframe, args.since, args.until
    )
    if not candles:
        parser.error("no candles found; run scripts.download for this range first")
    interval = TIMEFRAMES_MS[args.timeframe]
    if (candles[0].timestamp_ms != args.since or candles[-1].timestamp_ms + interval != args.until
            or len(candles) * interval != args.until - args.since):
        parser.error("incomplete requested candle coverage")
    if args.strategy == "intraday":
        warmup_required = 243
    elif args.strategy == "sma":
        warmup_required = args.slow
    elif args.strategy == "momentum":
        warmup_required = args.lookback + 1
    elif args.strategy == "mean-reversion":
        warmup_required = args.lookback
    else:
        warmup_required = 1
    if args.risk_regime == "slow_slope":
        warmup_required = max(warmup_required, 186)
    interval = TIMEFRAMES_MS[args.timeframe]
    warmup_since_ms = max(0, args.since - warmup_required * interval)
    warmup_candles = (
        repository.list_range(
            settings.exchange_id,
            args.symbol,
            args.timeframe,
            warmup_since_ms,
            args.since,
        )
        if warmup_since_ms < args.since
        else []
    )
    signal_candles = warmup_candles + candles
    config = BacktestConfig(
        intraday_strong_close=args.intraday_strong_close,
        intraday_min_atr_fraction=args.intraday_min_atr_pct / 100,
        intraday_entry=args.intraday_entry,
        max_entries_per_day=args.max_entries_per_day or None,
        max_holding_bars=args.max_holding_bars or None,
        initial_cash=args.initial_cash,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        stop_loss_pct=args.stop_loss_pct / 100 if args.stop_loss_pct else None,
        take_profit_pct=args.take_profit_pct / 100 if args.take_profit_pct else None,
        leverage=args.leverage,
        risk_regime=args.risk_regime,
        risk_per_trade=args.risk_per_trade_pct / 100 if args.risk_per_trade_pct else None,
        max_exposure_fraction=args.max_exposure_pct / 100,
        exit_mode=args.exit_mode,
        stop_reentry_mode=args.stop_reentry_mode,
        trend_entry_buffer=args.trend_entry_buffer_pct / 100,
        trailing_activation=args.trailing_activation_pct / 100 if args.trailing_activation_pct else None,
        trailing_distance=args.trailing_distance_pct / 100 if args.trailing_distance_pct else None,
        trailing_reentry_mode=args.trailing_reentry_mode,
    )
    strategy = make_strategy(args.strategy, config, fast=args.fast, slow=args.slow,
                             lookback=args.lookback, momentum_threshold=args.momentum_threshold,
                             entry_deviation=args.entry_deviation)
    result = BacktestEngine(config).run(signal_candles, strategy, evaluation_start_ms=args.since)
    saved = BacktestRunRepository(settings.db_path).save_with_status(
        result, candles, config, args.stage, args.note,
        args.fast if args.strategy == "sma" else None,
        args.slow if args.strategy == "sma" else None,
        base_run_key=args.base_run_key, signal_candles=signal_candles,
        research_plan_id=args.research_plan_id,
    )
    payload = {
        "strategy": result.strategy_name,
        "run_key": saved.run.run_key,
        "strategy_key": saved.run.strategy_key,
        "created": saved.created,
        "research_plan_id": args.research_plan_id,
        "symbol": result.symbol,
        "timeframe": result.timeframe,
        "initial_cash": result.initial_cash,
        "final_equity": result.final_equity,
        "risk": {
            "stop_loss_pct": args.stop_loss_pct,
            "take_profit_pct": args.take_profit_pct,
            "leverage": args.leverage,
            "risk_per_trade_pct": args.risk_per_trade_pct,
            "max_exposure_pct": args.max_exposure_pct,
            "exit_mode": args.exit_mode,
            "stop_reentry_mode": args.stop_reentry_mode,
            "trend_entry_buffer_pct": args.trend_entry_buffer_pct,
            "trailing_activation_pct": args.trailing_activation_pct,
            "trailing_distance_pct": args.trailing_distance_pct,
            "trailing_reentry_mode": args.trailing_reentry_mode,
        },
        "metrics": _finite_dict(asdict(result.metrics)),
        "period": {
            "since_ms": candles[0].timestamp_ms,
            "until_ms": candles[-1].timestamp_ms,
            "candles": len(candles),
            "warmup_candles": len(warmup_candles),
        },
    }
    print(json.dumps(payload, indent=2, allow_nan=False))


def _finite_dict(values: dict[str, float | int]) -> dict[str, float | int | None]:
    return {
        key: value if not isinstance(value, float) or isfinite(value) else None
        for key, value in values.items()
    }


if __name__ == "__main__":
    main()
