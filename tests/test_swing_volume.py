from dataclasses import replace

import pytest

from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from app.strategies.swing_volume import DirectionalSwingVolumeStrategy
from tests.test_swing_efficiency import history


@pytest.mark.parametrize('short',[False,True])
def test_completed_volume_gate_preserves_equal_threshold_and_blocks_only_new_entries(short):
    bars=history(short,False)
    parent=DirectionalSwingEfficiencyStrategy().generate(bars)
    candidate=DirectionalSwingVolumeStrategy()
    equal=candidate.generate(bars)
    assert equal.direction==parent.direction==(-1 if short else 1)
    assert equal.stop_loss_price==parent.stop_loss_price
    # Current 4h total 3.9 versus preceding 20*4h mean 4.
    bars[-1]=replace(bars[-1],volume=.9)
    blocked=candidate.generate(bars)
    assert blocked.direction==0
    assert (blocked.exit_long,blocked.exit_short)==(parent.exit_long,parent.exit_short)
    assert candidate.generate(bars[:-1]).direction==0
    future=replace(bars[-1],timestamp_ms=bars[-1].timestamp_ms+3600000,volume=100000)
    assert candidate.generate((bars+[future])[:-1])==blocked
    # A low-volume bar still triggers the original exit on a clear reversal.
    price=300 if short else 100
    exiting=bars[:-4]+[replace(c,open=price,high=price+1,low=price-1,close=price,volume=.1) for c in bars[-4:]]
    a,b=DirectionalSwingEfficiencyStrategy().generate(exiting),candidate.generate(exiting)
    assert (a.exit_long,a.exit_short)==(b.exit_long,b.exit_short)
    assert b.exit_short if short else b.exit_long
