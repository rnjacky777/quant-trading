from dataclasses import replace

import pytest

from app.data.models import Candle
from app.strategies.directional_swing import DirectionalSwingStrategy
from app.strategies.swing_confirmation import DirectionalSwingConfirmationStrategy


def history(short: bool) -> list[Candle]:
    prices = [100 + i for i in range(60)] + [170, 172]
    if short:
        prices = [400 - p for p in prices]
    return [Candle("test", "BTC/USDT", "1h", i * 3600000,
                   prices[i // 4], prices[i // 4] + 1,
                   prices[i // 4] - 1, prices[i // 4], 1)
            for i in range(len(prices) * 4)]


@pytest.mark.parametrize("short", [False, True])
def test_waits_for_full_next_four_hour_close_and_preserves_exit_and_stop(short):
    bars = history(short)
    strategy = DirectionalSwingConfirmationStrategy()
    assert DirectionalSwingStrategy().generate(bars[:-4]).direction == (-1 if short else 1)
    assert strategy.generate(bars[:-4]).direction == 0
    assert strategy.generate(bars[:-1]).direction == 0
    signal = strategy.generate(bars)
    assert signal.direction == (-1 if short else 1)
    assert signal.timestamp.timestamp() * 1000 == bars[-1].timestamp_ms
    baseline = DirectionalSwingStrategy().generate(bars)
    assert signal.stop_loss_price == baseline.stop_loss_price
    assert (signal.exit_long, signal.exit_short) == (baseline.exit_long, baseline.exit_short)


@pytest.mark.parametrize("short", [False, True])
def test_wick_and_equal_close_do_not_confirm_or_use_future_bar(short):
    bars = history(short)
    strategy = DirectionalSwingConfirmationStrategy()
    for close in (230 if short else 170, 231 if short else 169):
        altered = bars[:-1] + [replace(bars[-1], close=close,
            high=max(bars[-1].high, close), low=min(bars[-1].low, close))]
        assert strategy.generate(altered).direction == 0
    signal = strategy.generate(bars)
    future = replace(bars[-1], timestamp_ms=bars[-1].timestamp_ms + 3600000, low=99, close=100)
    assert strategy.generate((bars + [future])[:-1]) == signal


def test_previous_bar_must_have_been_a_real_breakout():
    bars = history(False)
    # Prior high invalidates the preceding breakout but not the confirmation high.
    bars[59 * 4] = replace(bars[59 * 4], high=171)
    assert DirectionalSwingConfirmationStrategy().generate(bars).direction == 0
