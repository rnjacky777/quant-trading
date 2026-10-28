import pytest

from app.data.models import Candle
from app.strategies.directional_swing import DirectionalSwingStrategy


@pytest.mark.parametrize("short", [False, True])
def test_faster_channel_exits_before_original_channel_for_both_sides(short):
    prices = [100 + i for i in range(60)] + [152]
    if short:
        prices = [300 - p for p in prices]
    bars = [Candle("test", "BTC/USDT", "1h", i * 3600000,
                  prices[i // 4], prices[i // 4] + .1,
                  prices[i // 4] - .1, prices[i // 4], 1) for i in range(244)]
    old = DirectionalSwingStrategy().generate(bars)
    new = DirectionalSwingStrategy(5).generate(bars)
    assert (new.exit_short if short else new.exit_long)
    assert not (old.exit_short if short else old.exit_long)
    assert new.direction == old.direction
    assert new.stop_loss_price == old.stop_loss_price
    # The fourth hour completes the new 4H close; earlier hours cannot use it.
    before = DirectionalSwingStrategy(5).generate(bars[:-1])
    assert not (before.exit_short if short else before.exit_long)


@pytest.mark.parametrize("value", [0, 60, True, 5.5])
def test_exit_channel_rejects_invalid_lookback(value):
    with pytest.raises(ValueError):
        DirectionalSwingStrategy(value)
