from dataclasses import replace

import pytest

from app.data.models import Candle
from app.strategies.pa_smc import DirectionalSweepStrategy
from app.strategies.sweep_window import DirectionalSweepWindowStrategy


def history(short=False, waits=2):
    bars = [Candle("test", "BTC/USDT", "1h", i*3600000,
                   100+i*.1, 100+i*.1+.01, 100+i*.1-.01, 100+i*.1, 1) for i in range(242)]
    def add(o,h,l,c):
        bars.append(Candle("test", "BTC/USDT", "1h", len(bars)*3600000,o,h,l,c,1))
    add(123.4,124.5,115,123)
    for _ in range(waits):
        add(123.9,124.4,123.6,124)
    add(124.7,125.1,124.6,125)
    if short:
        bars = [replace(c,open=250-c.open,high=250-c.low,low=250-c.high,close=250-c.close) for c in bars]
    return bars


@pytest.mark.parametrize("short", [False, True])
def test_delayed_confirmation_increases_window_but_expires_after_three_hours(short):
    candidate = DirectionalSweepWindowStrategy()
    bars = history(short)
    assert DirectionalSweepStrategy().generate(bars).direction == 0
    assert candidate.generate(bars).direction == (-1 if short else 1)
    assert candidate.generate(bars[:-1]).direction == 0
    assert candidate.generate(history(short,waits=3)).direction == 0
    immediate = history(short,waits=0)
    old,new = DirectionalSweepStrategy().generate(immediate),candidate.generate(immediate)
    assert new.direction == old.direction == (-1 if short else 1)
    assert new.stop_loss_price == old.stop_loss_price
    assert (new.exit_long,new.exit_short) == (old.exit_long,old.exit_short)


def test_invalidated_sweep_and_already_crossed_level_cannot_reconfirm():
    candidate = DirectionalSweepWindowStrategy()
    bars=history()
    bars[243]=replace(bars[243],open=115,high=124.4,low=114,close=114.5)
    assert candidate.generate(bars).direction == 0
    bars=history()
    bars[243]=replace(bars[243],high=124.9,close=124.8)
    assert candidate.generate(bars).direction == 0
