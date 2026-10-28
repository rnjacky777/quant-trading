from dataclasses import replace

import pytest

from app.data.models import Candle
from app.strategies.swing_confirmation import DirectionalSwingConfirmationStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy, path_efficiency


def history(short: bool, choppy: bool) -> list[Candle]:
    prices = ([100.] * 40 + [140., 160.] * 10 if choppy else [100. + i for i in range(60)]) + [170., 172.]
    if short:
        prices = [400 - p for p in prices]
    return [Candle("test", "BTC/USDT", "1h", i * 3600000, prices[i // 4],
                   prices[i // 4] + 1, prices[i // 4] - 1, prices[i // 4], 1)
            for i in range(248)]


@pytest.mark.parametrize("short", [False, True])
def test_filter_blocks_choppy_but_preserves_directional_entries_and_exits(short):
    parent, candidate = DirectionalSwingConfirmationStrategy(), DirectionalSwingEfficiencyStrategy()
    choppy = history(short, True)
    original = parent.generate(choppy)
    filtered = candidate.generate(choppy)
    assert original.direction == (-1 if short else 1)
    assert filtered.direction == 0
    assert (filtered.exit_long, filtered.exit_short) == (original.exit_long, original.exit_short)
    trending = history(short, False)
    old, new = parent.generate(trending), candidate.generate(trending)
    assert new.direction == old.direction == (-1 if short else 1)
    assert new.stop_loss_price == old.stop_loss_price
    assert candidate.generate(trending[:-1]).direction == 0
    future = replace(trending[-1], timestamp_ms=trending[-1].timestamp_ms + 3600000)
    assert candidate.generate((trending + [future])[:-1]) == new
    # Existing position exits remain active even when new entries are blocked.
    p = 300 if short else 100
    exiting = choppy[:-4] + [replace(c, open=p, high=p+1, low=p-1, close=p) for c in choppy[-4:]]
    old, new = parent.generate(exiting), candidate.generate(exiting)
    assert (new.exit_long, new.exit_short) == (old.exit_long, old.exit_short)
    assert new.exit_short if short else new.exit_long


def test_efficiency_uses_path_length_and_is_scale_and_direction_invariant():
    assert path_efficiency([100, 101, 102]) == 1
    assert path_efficiency([102, 101, 100]) == 1
    assert path_efficiency([100, 100, 100]) == 0
    assert path_efficiency([100, 110, 100]) == 0
    prices = [100, 110, 105, 113]
    assert path_efficiency(prices) == pytest.approx(13 / 23)
    assert path_efficiency([p * 2 for p in prices]) == path_efficiency(prices)
