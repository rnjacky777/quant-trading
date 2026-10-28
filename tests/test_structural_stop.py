from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.backtest.frozen_entry import FrozenEntryStrategy
from app.data.models import Candle
from app.strategies.base import Action
from app.strategies.directional_intraday import DirectionalSignal
from app.strategies.pa_smc import DirectionalSweepStrategy
from app.strategies.sweep_structural_stop import DirectionalSweepStructuralStopStrategy
from app.strategies.sweep_context_exit import DirectionalSweepContextExitStrategy
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy


def history(short=False):
    prices=[200-i*.1 if short else 100+i*.1 for i in range(244)]
    bars=[Candle("test","BTC/USDT","1h",i*3600000,p,p+.01,p-.01,p,1) for i,p in enumerate(prices)]
    if short:
        bars[-2]=replace(bars[-2],open=176.8,high=195,low=175.5,close=176.6)
        bars[-1]=replace(bars[-1],open=175.3,high=175.4,low=174.9,close=175)
    else:
        bars[-2]=replace(bars[-2],open=123.4,high=124.5,low=115,close=123)
        bars[-1]=replace(bars[-1],open=124.7,high=125.1,low=124.6,close=125)
    return bars


@pytest.mark.parametrize("short",[False,True])
def test_structural_stop_changes_only_known_extreme_not_entry_or_exit_flags(short):
    bars=history(short)
    old=DirectionalSweepStrategy().generate(bars)
    strategy=DirectionalSweepStructuralStopStrategy()
    new=strategy.generate(bars)
    for field in ('symbol','timestamp','action','strength','direction','exit_long','exit_short'):
        assert getattr(new,field)==getattr(old,field)
    assert new.direction==(-1 if short else 1)
    assert new.stop_loss_price==(bars[-2].high if short else bars[-2].low)
    assert strategy.generate(bars[:-1]).direction==0
    assert strategy.generate(bars[:-1]).stop_loss_price is None
    future=replace(bars[-1],timestamp_ms=bars[-1].timestamp_ms+3600000)
    assert strategy.generate((bars+[future])[:-1])==new


def test_frozen_entry_preserves_original_future_exits_but_cannot_add_entries():
    bars=[Candle("test","BTC/USDT","1h",i*3600000,100,101,99,100,1) for i in range(3)]
    signals={c.timestamp_ms:DirectionalSignal("BTC/USDT",datetime.fromtimestamp(c.timestamp_ms/1000,timezone.utc),
        Action.BUY,1,"source",stop_loss_price=80,direction=1,exit_long=i==2) for i,c in enumerate(bars)}
    wrapper=FrozenEntryStrategy(3600000,signals)
    assert wrapper.generate(bars[:1])==signals[0]
    later=wrapper.generate(bars[:2])
    assert later.direction==0 and later.action is Action.HOLD and later.stop_loss_price is None
    exit_signal=wrapper.generate(bars)
    assert exit_signal.direction==0 and exit_signal.exit_long
    assert wrapper.generate(bars[:1])==signals[0]
    with pytest.raises(ValueError):
        wrapper.generate([])


@pytest.mark.parametrize("short",[False,True])
def test_context_exit_removes_only_hourly_channel_exit_while_four_hour_trend_stays_valid(short):
    bars=[Candle("test","BTC/USDT","1h",i*3600000,100+i*.1,100+i*.1+.01,
                 100+i*.1-.01,100+i*.1,1) for i in range(244)]
    bars[-1]=replace(bars[-1],open=121,high=121.1,low=120.9,close=121)
    if short:
        bars=[replace(c,open=300-c.open,high=300-c.low,low=300-c.high,close=300-c.close) for c in bars]
    old=DirectionalSweepStructuralStopStrategy().generate(bars)
    new=DirectionalSweepContextExitStrategy().generate(bars)
    assert old.exit_short if short else old.exit_long
    assert not (new.exit_short if short else new.exit_long)
    assert old.direction==new.direction and old.stop_loss_price==new.stop_loss_price
    assert new.exit_long if short else new.exit_short  # Opposite 4h direction still invalidates.


@pytest.mark.parametrize("short",[False,True])
def test_context_exit_preserves_entry_and_structure_stop_and_causal_timestamp(short):
    bars=history(short)
    old=DirectionalSweepStructuralStopStrategy().generate(bars)
    strategy=DirectionalSweepContextExitStrategy();new=strategy.generate(bars)
    assert old.direction==new.direction==(-1 if short else 1)
    for field in ('action','strength','timestamp','stop_loss_price'):
        assert getattr(new,field)==getattr(old,field)
    assert new.exit_long if short else new.exit_short
    future=replace(bars[-1],timestamp_ms=bars[-1].timestamp_ms+3600000)
    assert strategy.generate((bars+[future])[:-1])==new


@pytest.mark.parametrize("short",[False,True])
def test_structure_confirmation_requires_close_past_all_three_known_bars(short):
    bars=history(short)
    parent=DirectionalSweepStructuralStopStrategy();candidate=DirectionalSweepStructureConfirmStrategy()
    old,new=parent.generate(bars),candidate.generate(bars)
    assert old.direction==new.direction==(-1 if short else 1)
    assert old.stop_loss_price==new.stop_loss_price
    if short:
        bars[-3]=replace(bars[-3],low=174)
    else:
        bars[-3]=replace(bars[-3],high=126)
    old,new=parent.generate(bars),candidate.generate(bars)
    assert old.direction==(-1 if short else 1) and new.direction==0
    assert (old.exit_long,old.exit_short)==(new.exit_long,new.exit_short)


@pytest.mark.parametrize("short",[False,True])
def test_structure_confirmation_rejects_equality_and_wick_only_break(short):
    candidate=DirectionalSweepStructureConfirmStrategy()
    for level in ((175,174.95) if short else (125,125.05)):
        bars=history(short)
        bars[-3]=replace(bars[-3],low=level) if short else replace(bars[-3],high=level)
        assert candidate.generate(bars).direction==0
    bars=history(short);signal=candidate.generate(bars)
    future=replace(bars[-1],timestamp_ms=bars[-1].timestamp_ms+3600000)
    assert candidate.generate((bars+[future])[:-1])==signal
