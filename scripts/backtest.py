import argparse
from dataclasses import asdict
from datetime import datetime
import json
from math import isfinite

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.config.settings import Settings
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
    args = parser.parse_args()

    settings = Settings.from_env()
    candles = CandleRepository(settings.db_path).list_range(
        settings.exchange_id, args.symbol, args.timeframe, args.since, args.until
    )
    if not candles:
        parser.error("no candles found; run scripts.download for this range first")
    strategy = (
        MovingAverageTrendStrategy(args.fast, args.slow)
        if args.strategy == "sma"
        else BuyAndHoldStrategy()
    )
    result = BacktestEngine(BacktestConfig(
        initial_cash=args.initial_cash,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
    )).run(candles, strategy)
    payload = {
        "strategy": result.strategy_name,
        "symbol": result.symbol,
        "timeframe": result.timeframe,
        "initial_cash": result.initial_cash,
        "final_equity": result.final_equity,
        "metrics": _finite_dict(asdict(result.metrics)),
        "period": {
            "since_ms": candles[0].timestamp_ms,
            "until_ms": candles[-1].timestamp_ms,
            "candles": len(candles),
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
