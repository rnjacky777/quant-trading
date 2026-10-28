from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.backtest.reentry import PullbackReentry
from app.data.models import Candle, TIMEFRAMES_MS
from app.strategies.base import Action, Signal


STEP = TIMEFRAMES_MS["4h"]


def bar(i, close, *, open_=None, low=None, high=None):
    return Candle("test", "BTC/USDT", "4h", i * STEP, open_ or close,
                  high or close, low or close, close, 1)


class LongSignal:
    name = "test"

    def __init__(self, hold=False):
        self.hold = hold

    def generate(self, candles):
        last = candles[-1]
        action = Action.HOLD if self.hold and len(candles) == 190 else Action.BUY
        return Signal(last.symbol, datetime.fromtimestamp(last.timestamp_ms / 1000, timezone.utc),
                      action, 1, self.name)


def history():
    return [bar(i, 100 + .1 * i) for i in range(186)] + [
        bar(186, 130, open_=119, low=119, high=131),
        bar(187, 124, open_=130, low=123, high=130),
        bar(188, 110), bar(189, 135), bar(190, 135), bar(191, 135)]


def config():
    return BacktestConfig(fee_bps=0, slippage_bps=0, stop_loss_pct=.05,
                          trailing_activation=.05, trailing_distance=.05,
                          stop_reentry_mode="signal_reset", trailing_reentry_mode="pullback_reclaim")


@pytest.mark.parametrize("hold,expected", [(False, 190), (True, 191)])
def test_reclaim_requires_later_pullback_completed_recovery_buy_and_next_bar(hold, expected):
    tape = history()
    engine = BacktestEngine(config())
    result = engine.run(tape, LongSignal(hold), evaluation_start_ms=186 * STEP)
    assert result.trades[0].exit_reason == "trailing_stop"
    assert [t.entry_timestamp_ms for t in result.trades] == [186 * STEP, expected * STEP]
    assert result.trades[1].entry_price == tape[expected].open
    assert engine.run(tape, LongSignal(hold), evaluation_start_ms=186 * STEP) == result


def test_reclaim_does_not_unlock_initial_stop_or_use_entry_candle_close():
    tape = history()
    tape[186] = replace(tape[186], low=110)
    result = BacktestEngine(config()).run(tape, LongSignal(), evaluation_start_ms=186 * STEP)
    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "stop_loss"
    tape = history()
    tape[189] = bar(189, 110)  # Only execution-bar close recovers; cannot enter yet.
    result = BacktestEngine(config()).run(tape, LongSignal(), evaluation_start_ms=186 * STEP)
    assert result.trades[1].entry_timestamp_ms == 191 * STEP


def test_gate_ignores_exit_bar_equality_high_only_and_nonpositive_trend():
    gate = PullbackReentry()
    tape = [bar(i, 100) for i in range(186)]
    gate.arm(tape[-1].timestamp_ms)
    assert not gate.observe(tape, Action.BUY)
    tape.append(bar(186, 99, high=120))
    assert not gate.observe(tape, Action.BUY)
    assert gate.pullback_seen
    tape.append(bar(187, 100, high=120))
    assert not gate.observe(tape, Action.BUY)  # Flat/down SMA180, despite recovery.
    gate.reset()
    assert not gate.observe(tape + [bar(188, 150)], Action.BUY)
