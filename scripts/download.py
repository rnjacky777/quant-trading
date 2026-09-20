import argparse
from datetime import datetime

from app.config.settings import Settings
from app.data.downloader import download_candles
from app.data.repository import CandleRepository
from app.exchange.ccxt_client import CcxtHistoricalProvider


def utc_milliseconds(value: str) -> int:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("timestamp needs a UTC offset")
    return int(parsed.timestamp() * 1000)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download closed crypto candles")
    parser.add_argument("--symbol", choices=["BTC/USDT", "ETH/USDT"], required=True)
    parser.add_argument("--timeframe", choices=["4h", "1d"], required=True)
    parser.add_argument("--since", type=utc_milliseconds, required=True)
    parser.add_argument("--until", type=utc_milliseconds, required=True)
    args = parser.parse_args()

    settings = Settings.from_env()
    provider = CcxtHistoricalProvider(settings.exchange_id)
    candles = download_candles(
        provider, args.symbol, args.timeframe, args.since, args.until
    )
    count = CandleRepository(settings.db_path).upsert(candles)
    print(f"Stored {count} closed candles in {settings.db_path}")


if __name__ == "__main__":
    main()
