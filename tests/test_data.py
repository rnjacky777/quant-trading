from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.data.downloader import download_candles
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository


STEP = TIMEFRAMES_MS["4h"]


class FakeProvider:
    exchange_id = "fake"

    def __init__(self, rows: list[list[float]]) -> None:
        self.rows = rows

    def fetch_ohlcv(
        self, symbol: str, timeframe: str, since_ms: int, limit: int
    ) -> list[list[float]]:
        return [row for row in self.rows if row[0] >= since_ms][:limit]


class DataTests(unittest.TestCase):
    def test_pagination_excludes_current_candle_and_is_idempotent(self) -> None:
        rows = [[i * STEP, 100, 110, 90, 105, 2] for i in range(4)]
        candles = download_candles(
            FakeProvider(rows), "BTC/USDT", "4h", 0, 4 * STEP,
            page_size=2, now_ms=3 * STEP + 100,
        )
        self.assertEqual([c.timestamp_ms for c in candles], [0, STEP, 2 * STEP])
        with TemporaryDirectory() as directory:
            repository = CandleRepository(Path(directory) / "candles.sqlite3")
            self.assertEqual(repository.upsert(candles), 3)
            repository.upsert(candles)
            self.assertEqual(repository.list_candles("fake", "BTC/USDT", "4h"), candles)

    def test_bad_ohlc_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Candle("fake", "BTC/USDT", "4h", 0, 100, 99, 90, 105, 2)

    def test_nonadvancing_provider_is_rejected(self) -> None:
        class Stalled(FakeProvider):
            def fetch_ohlcv(self, symbol, timeframe, since_ms, limit):
                return [[0, 100, 110, 90, 105, 2]]

        with self.assertRaises(ValueError):
            download_candles(Stalled([]), "BTC/USDT", "4h", STEP, 3 * STEP,
                             now_ms=5 * STEP)

    def test_invalid_time_range_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            download_candles(FakeProvider([]), "ETH/USDT", "1d", 1, 1)


if __name__ == "__main__":
    unittest.main()
