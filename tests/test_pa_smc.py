from dataclasses import replace

from app.data.models import Candle
from app.strategies.pa_smc import DirectionalSweepStrategy


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


def test_sweep_needs_later_completed_confirmation_for_both_sides():
    strategy=DirectionalSweepStrategy()
    for short in (False,True):
        bars=history(short)
        signal=strategy.generate(bars)
        assert signal.direction==(-1 if short else 1)
        assert strategy.generate(bars[:-1]).direction==0
        assert signal.timestamp.timestamp()*1000==bars[-1].timestamp_ms
        future=replace(bars[-1],timestamp_ms=bars[-1].timestamp_ms+3600000)
        assert strategy.generate((bars+[future])[:-1])==signal


def test_wick_only_confirmation_and_touch_without_sweep_do_not_enter():
    strategy=DirectionalSweepStrategy()
    bars=history()
    bars[-1]=replace(bars[-1],open=123,low=122.9,close=124.4)
    assert strategy.generate(bars).direction==0  # High crossed, close did not.
    bars=history()
    old_low=min(c.low for c in bars[-22:-2])
    bars[-2]=replace(bars[-2],low=old_low)
    assert strategy.generate(bars).direction==0
    bars=history(True)
    bars[-1]=replace(bars[-1],open=176,high=176,close=175.6)
    assert strategy.generate(bars).direction==0
