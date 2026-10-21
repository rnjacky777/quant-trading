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


def market_candle(index: int, open_: float, high: float, low: float, close: float) -> Candle:
    return Candle("test", "BTC/USDT", "1d", index * STEP, open_, high, low, close, 1)


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


def test_indicator_warmup_is_used_without_counting_pre_period_performance() -> None:
    strategy = MovingAverageTrendStrategy(fast_period=1, slow_period=2)
    candles = [
        candle(0, 100),
        candle(1, 110),
        candle(2, 120),
        candle(3, 130),
    ]
    without_warmup = BacktestEngine(
        BacktestConfig(fee_bps=0, slippage_bps=0)
    ).run(candles[2:], strategy)
    with_warmup = BacktestEngine(
        BacktestConfig(fee_bps=0, slippage_bps=0)
    ).run(candles, strategy, evaluation_start_ms=2 * STEP)

    assert without_warmup.metrics.number_of_trades == 0
    assert with_warmup.metrics.number_of_trades == 1
    assert with_warmup.trades[0].entry_timestamp_ms == 2 * STEP
    assert with_warmup.final_equity == pytest.approx(10_833.333333)


def test_missing_candle_is_rejected() -> None:
    with pytest.raises(ValueError, match="missing interval"):
        BacktestEngine().run([candle(0, 100), candle(2, 100)], AlwaysLong())


def test_stop_loss_and_take_profit_use_intrabar_prices() -> None:
    stopped = BacktestEngine(BacktestConfig(
        fee_bps=0, slippage_bps=0, stop_loss_pct=0.10, take_profit_pct=0.20
    )).run(
        [candle(0, 100), market_candle(1, 100, 125, 85, 110)], AlwaysLong()
    )
    assert stopped.final_equity == pytest.approx(9_000)
    assert stopped.trades[0].exit_reason == "stop_loss"
    assert stopped.trades[0].stop_loss_price == pytest.approx(90)
    assert stopped.trades[0].take_profit_price == pytest.approx(120)


def test_leverage_scales_pnl_and_is_recorded() -> None:
    result = BacktestEngine(BacktestConfig(
        fee_bps=0, slippage_bps=0, leverage=2
    )).run(
        [candle(0, 100), candle(1, 100), candle(2, 110)], AlwaysLong()
    )
    assert result.final_equity == pytest.approx(12_000)
    assert result.trades[0].return_pct == pytest.approx(0.20)
    assert result.trades[0].leverage == 2
