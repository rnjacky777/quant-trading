from dataclasses import replace

import pytest

from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.sweep_no_atr_floor import DirectionalSweepNoAtrFloorStrategy
from tests.test_structural_stop import history


@pytest.mark.parametrize('short',[False,True])
def test_lower_atr_shape_keeps_known_stop_exits_and_causal_timing(short):
    bars=history(short)
    sweep=bars[-2]
    if short:
        bars[-2]=replace(sweep,high=max(c.high for c in bars[-22:-2])+.01)
    else:
        bars[-2]=replace(sweep,low=min(c.low for c in bars[-22:-2])-.01)
    parent=DirectionalSweepStructureConfirmStrategy().generate(bars)
    child=DirectionalSweepNoAtrFloorStrategy().generate(bars)
    assert parent.direction==0 and child.direction==(-1 if short else 1)
    assert child.stop_loss_price==(bars[-2].high if short else bars[-2].low)
    assert (child.exit_long,child.exit_short)==(parent.exit_long,parent.exit_short)
    assert DirectionalSweepNoAtrFloorStrategy().generate(bars[:-1]).direction==0
    future=replace(bars[-1],timestamp_ms=bars[-1].timestamp_ms+3600000,high=9999)
    assert DirectionalSweepNoAtrFloorStrategy().generate((bars+[future])[:-1])==child


@pytest.mark.parametrize('short',[False,True])
def test_original_high_atr_entries_are_preserved_and_shape_is_still_required(short):
    bars=history(short)
    p=DirectionalSweepStructureConfirmStrategy().generate(bars)
    c=DirectionalSweepNoAtrFloorStrategy().generate(bars)
    assert p.direction==c.direction==(-1 if short else 1)
    assert p.stop_loss_price==c.stop_loss_price
    bars[-1]=replace(bars[-1],close=bars[-1].open)
    assert DirectionalSweepNoAtrFloorStrategy().generate(bars).direction==0
