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


def test_stop_reentry_waits_for_sell_then_buy_and_hold_does_not_reset() -> None:
    class Scripted:
        name = "scripted"
        def generate(self, candles):
            point = candles[-1]
            actions = [Action.BUY, Action.BUY, Action.HOLD, Action.BUY, Action.SELL, Action.BUY, Action.BUY]
            return Signal(point.symbol, datetime.fromtimestamp(point.timestamp_ms/1000, timezone.utc),
                          actions[len(candles)-1], 1, self.name)
    bars = [market_candle(i, 100, 100, 90 if i in (1, 2) else 100, 100) for i in range(8)]
    config = BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=0.05, stop_reentry_mode="signal_reset")
    result = BacktestEngine(config).run(bars, Scripted())
    assert [trade.entry_timestamp_ms for trade in result.trades] == [STEP, 6*STEP]
    assert [trade.exit_reason for trade in result.trades] == ["stop_loss", "end_of_data"]
    # Engine instances do not retain the block between independent runs.
    assert BacktestEngine(config).run(bars, Scripted()) == result
    immediate = BacktestEngine(BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=0.05)).run(bars, Scripted())
    assert len(immediate.trades) > len(result.trades)


def test_signal_reset_does_not_block_reentry_after_take_profit() -> None:
    bars = [candle(0, 100), market_candle(1, 100, 120, 100, 110), candle(2, 110)]
    config = BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=0.05,
                            take_profit_pct=0.1, stop_reentry_mode="signal_reset")
    result = BacktestEngine(config).run(bars, AlwaysLong())
    assert [trade.exit_reason for trade in result.trades] == ["take_profit", "end_of_data"]
    with pytest.raises(ValueError, match="stop_reentry_mode"):
        BacktestConfig(stop_reentry_mode="unknown")


def test_trailing_stop_uses_completed_closes_next_bar_only_and_never_decreases() -> None:
    config = BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=0.05,
                            trailing_activation=0.05, trailing_distance=0.05)
    bars = [candle(0,100), market_candle(1,100,108,97,106),
            market_candle(2,106,108,101,105), market_candle(3,105,106,100,102)]
    result = BacktestEngine(config).run(bars, AlwaysLong())
    assert result.trades[0].exit_timestamp_ms == 3*STEP
    assert result.trades[0].exit_reason == "trailing_stop"
    assert result.trades[0].exit_price == pytest.approx(106*0.95)
    # Low=97 on the activation candle cannot trigger its future stop=100.7.
    # Lower close=105 cannot lower the already-raised stop.


def test_intrabar_high_does_not_activate_close_based_trailing_stop() -> None:
    config = BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=0.05,
                            trailing_activation=0.05, trailing_distance=0.05)
    bars = [candle(0,100), market_candle(1,100,110,97,101), market_candle(2,100,101,94,96)]
    trade = BacktestEngine(config).run(bars, AlwaysLong()).trades[0]
    assert trade.exit_reason == "stop_loss"
    assert trade.exit_price == pytest.approx(95)


def test_trailing_gap_fill_and_reentry_gate() -> None:
    config = BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=0.05,
                            trailing_activation=0.05, trailing_distance=0.05, stop_reentry_mode="signal_reset")
    bars = [candle(0,100), market_candle(1,100,111,99,110),
            market_candle(2,90,92,89,91), candle(3,92)]
    engine = BacktestEngine(config)
    result = engine.run(bars, AlwaysLong())
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "trailing_stop"
    assert result.trades[0].exit_price == 90
    assert engine.run(bars, AlwaysLong()) == result


def test_trailing_stop_precedes_target_if_both_touched() -> None:
    config = BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=0.05, take_profit_pct=0.20,
                            trailing_activation=0.05, trailing_distance=0.05)
    bars = [candle(0,100), market_candle(1,100,111,99,110), market_candle(2,110,125,100,115)]
    trade = BacktestEngine(config).run(bars, AlwaysLong()).trades[0]
    assert trade.exit_reason == "trailing_stop"
    assert trade.exit_price == pytest.approx(104.5)


@pytest.mark.parametrize("kwargs", [dict(trailing_activation=0.05), dict(trailing_distance=0.05),
                                    dict(trailing_activation=float("nan"),trailing_distance=0.05),
                                    dict(trailing_activation=0.05,trailing_distance=1),
                                    dict(trailing_activation=0.05,trailing_distance=0.05,leverage=2)])
def test_trailing_configuration_rejects_incomplete_or_unsupported_rules(kwargs) -> None:
    with pytest.raises(ValueError):
        BacktestConfig(stop_loss_pct=0.05, **kwargs)


@pytest.mark.parametrize("hold_at_confirmation,expected_entry", [(False,6),(True,7)])
def test_trailing_breakout_requires_completed_close_and_buy_then_next_bar(hold_at_confirmation, expected_entry) -> None:
    class ConfirmationStrategy(AlwaysLong):
        def generate(self, candles):
            signal = super().generate(candles)
            if hold_at_confirmation and len(candles) == 6:
                from dataclasses import replace
                return replace(signal, action=Action.HOLD)
            return signal
    config = BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=0.05,
                            trailing_activation=0.05, trailing_distance=0.05,
                            stop_reentry_mode="signal_reset", trailing_reentry_mode="exit_high_breakout")
    bars = [candle(0,100), market_candle(1,100,111,99,110),
            market_candle(2,110,112,103,110), market_candle(3,110,120,108,111),
            market_candle(4,111,113,109,112), market_candle(5,112,115,111,113),
            market_candle(6,114,116,113,115), candle(7,115)]
    engine = BacktestEngine(config)
    result = engine.run(bars, ConfirmationStrategy())
    assert result.trades[0].exit_reason == "trailing_stop"
    assert result.trades[0].exit_timestamp_ms == 2*STEP
    assert [t.entry_timestamp_ms for t in result.trades] == [STEP, expected_entry*STEP]
    assert result.trades[1].entry_price == bars[expected_entry].open
    assert engine.run(bars, ConfirmationStrategy()) == result


def test_trailing_breakout_does_not_unlock_an_initial_stop() -> None:
    config = BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=0.05,
                            trailing_activation=0.05, trailing_distance=0.05,
                            stop_reentry_mode="signal_reset", trailing_reentry_mode="exit_high_breakout")
    result = BacktestEngine(config).run([candle(0,100),market_candle(1,100,101,94,99),candle(2,120),candle(3,121)],AlwaysLong())
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "stop_loss"


def test_sell_resets_trailing_breakout_threshold_for_a_new_trend() -> None:
    class ResetStrategy(AlwaysLong):
        def generate(self, candles):
            from dataclasses import replace
            signal = super().generate(candles)
            return replace(signal,action=Action.SELL) if len(candles)==3 else signal
    config = BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=0.05,
                            trailing_activation=0.05, trailing_distance=0.05,
                            stop_reentry_mode="signal_reset", trailing_reentry_mode="exit_high_breakout")
    bars = [candle(0,100),market_candle(1,100,111,99,110),market_candle(2,110,112,103,110),candle(3,110),candle(4,111)]
    result = BacktestEngine(config).run(bars,ResetStrategy())
    assert [t.entry_timestamp_ms for t in result.trades] == [STEP,4*STEP]


def test_trailing_breakout_does_not_change_take_profit_reentry() -> None:
    config = BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=0.05,take_profit_pct=0.1,
                            trailing_activation=0.05, trailing_distance=0.05,
                            stop_reentry_mode="signal_reset", trailing_reentry_mode="exit_high_breakout")
    result = BacktestEngine(config).run([candle(0,100),market_candle(1,100,111,99,110),candle(2,110)],AlwaysLong())
    assert len(result.trades)==2
    assert result.trades[0].exit_reason=="take_profit"
    for kwargs in (dict(trailing_reentry_mode="unknown"),dict(trailing_reentry_mode="exit_high_breakout")):
        with pytest.raises(ValueError):
            BacktestConfig(**kwargs)
