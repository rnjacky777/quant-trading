import argparse
from dataclasses import asdict
from datetime import datetime
import json
from math import isfinite

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.config.settings import Settings
from app.data.models import TIMEFRAMES_MS
from app.data.repository import CandleRepository
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from app.strategies.trend_following import MovingAverageTrendStrategy


def utc_milliseconds(value: str) -> int:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("timestamp needs a UTC offset")
    return int(parsed.timestamp() * 1000)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a long/cash SMA trend backtest")
    parser.add_argument("--symbol", choices=["BTC/USDT", "ETH/USDT"], required=True)
    parser.add_argument("--timeframe", choices=["4h", "1d"], required=True)
    parser.add_argument("--since", type=utc_milliseconds, required=True)
    parser.add_argument("--until", type=utc_milliseconds, required=True)
    parser.add_argument("--strategy", choices=["sma", "buy-hold"], default="sma")
    parser.add_argument("--fast", type=int, default=20)
    parser.add_argument("--slow", type=int, default=60)
    parser.add_argument("--initial-cash", type=float, default=10_000)
    parser.add_argument("--fee-bps", type=float, default=10)
    parser.add_argument("--slippage-bps", type=float, default=5)
    parser.add_argument("--stop-loss-pct", type=float, default=0)
    parser.add_argument("--take-profit-pct", type=float, default=0)
    parser.add_argument("--leverage", type=float, default=1)
    args = parser.parse_args()

    settings = Settings.from_env()
    repository = CandleRepository(settings.db_path)
    candles = repository.list_range(
        settings.exchange_id, args.symbol, args.timeframe, args.since, args.until
    )
    if not candles:
        parser.error("no candles found; run scripts.download for this range first")
    strategy = (
        MovingAverageTrendStrategy(args.fast, args.slow)
        if args.strategy == "sma"
        else BuyAndHoldStrategy()
    )
    warmup_required = args.slow if args.strategy == "sma" else 1
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
    result = BacktestEngine(BacktestConfig(
        initial_cash=args.initial_cash,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        stop_loss_pct=args.stop_loss_pct / 100 if args.stop_loss_pct else None,
        take_profit_pct=args.take_profit_pct / 100 if args.take_profit_pct else None,
        leverage=args.leverage,
    )).run(signal_candles, strategy, evaluation_start_ms=args.since)
    payload = {
        "strategy": result.strategy_name,
        "symbol": result.symbol,
        "timeframe": result.timeframe,
        "initial_cash": result.initial_cash,
        "final_equity": result.final_equity,
        "risk": {
            "stop_loss_pct": args.stop_loss_pct,
            "take_profit_pct": args.take_profit_pct,
            "leverage": args.leverage,
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
