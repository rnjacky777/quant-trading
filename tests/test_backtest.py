from datetime import datetime, timezone

import pytest

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.data.models import Candle, TIMEFRAMES_MS
from app.strategies.base import Action, Signal
from app.strategies.trend_following import MovingAverageTrendStrategy


STEP = TIMEFRAMES_MS["1d"]


class AlwaysLong:
    name = "always_long"

    def generate(self, candles: list[Candle]) -> Signal:
        candle = candles[-1]
        return Signal(
            candle.symbol,
            datetime.fromtimestamp(candle.timestamp_ms / 1000, timezone.utc),
            Action.BUY,
            1.0,
            self.name,
        )


def candle(index: int, price: float) -> Candle:
    return Candle("test", "BTC/USDT", "1d", index * STEP, price, price, price, price, 1)


def test_signal_executes_on_next_bar_open() -> None:
    result = BacktestEngine(BacktestConfig(fee_bps=0, slippage_bps=0)).run(
        [candle(0, 100), candle(1, 200), candle(2, 300)], AlwaysLong()
    )
    assert result.final_equity == pytest.approx(15_000)
    assert result.trades[0].entry_price == 200
    assert result.trades[0].entry_timestamp_ms == STEP


def test_fees_and_slippage_are_charged_on_both_sides() -> None:
    result = BacktestEngine(BacktestConfig(fee_bps=10, slippage_bps=10)).run(
        [candle(0, 100), candle(1, 100)], AlwaysLong()
    )
    assert result.final_equity < result.initial_cash
    assert result.metrics.fees > 0
    assert result.metrics.slippage > 0
    assert result.metrics.number_of_trades == 1


def test_sma_strategy_emits_target_state() -> None:
    strategy = MovingAverageTrendStrategy(fast_period=1, slow_period=2)
    assert strategy.generate([candle(0, 100)]).action is Action.HOLD
    assert strategy.generate([candle(0, 100), candle(1, 110)]).action is Action.BUY
    assert strategy.generate([candle(0, 110), candle(1, 100)]).action is Action.SELL


def test_missing_candle_is_rejected() -> None:
    with pytest.raises(ValueError, match="missing interval"):
        BacktestEngine().run([candle(0, 100), candle(2, 100)], AlwaysLong())
