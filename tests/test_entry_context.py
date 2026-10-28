from dataclasses import replace

import pytest

from app.backtest.entry_context import entry_context
from app.data.models import Candle
from app.strategies.pa_smc import DirectionalSweepStrategy
from app.strategies.sweep_mean_guard import DirectionalSweepMeanGuardStrategy


@pytest.mark.parametrize("price,bucket",[(99,"at_or_behind_mean"),(100,"at_or_behind_mean"),
                                          (102,"0_to_1_atr"),(104,"1_to_2_atr"),(104.1,"above_2_atr")])
def test_extension_uses_completed_four_hour_atr_and_fixed_boundaries(price,bucket):
    bars=[Candle("test","BTC/USDT","1h",i*3600000,100,101,99,100,1) for i in range(84)]
    partial=Candle("test","BTC/USDT","1h",84*3600000,price,price,price,price,1)
    f=entry_context(bars+[partial],1,price+.1)
    assert f['completed_4h_sma20']==100 and f['completed_4h_atr14']==2
    assert f['extension_bucket']==bucket
    assert f['signed_extension_4h_atr']==pytest.approx((price-100)/2)
    assert f['gap_bucket']=='adverse'
    # An unfinished 4h bucket cannot alter its SMA or ATR even with a huge wick.
    altered=entry_context(bars+[replace(partial,high=1000,low=1)],1,price+.1)
    assert altered['completed_4h_sma20']==f['completed_4h_sma20']
    assert altered['completed_4h_atr14']==f['completed_4h_atr14']


def sweep_history(short=False):
    prices=[200-i*.1 if short else 100+i*.1 for i in range(244)]
    bars=[Candle("test","BTC/USDT","1h",i*3600000,p,p+.01,p-.01,p,1) for i,p in enumerate(prices)]
    if short:
        bars[-2]=replace(bars[-2],open=176.8,high=195,low=175.5,close=176.6)
        bars[-1]=replace(bars[-1],open=175.3,high=175.4,low=174.9,close=175)
    else:
        bars[-2]=replace(bars[-2],open=123.4,high=124.5,low=115,close=123)
        bars[-1]=replace(bars[-1],open=124.7,high=125.1,low=124.6,close=125)
    return bars


def test_mean_guard_preserves_longs_and_does_not_block_existing_short_exits():
    parent,candidate=DirectionalSweepStrategy(),DirectionalSweepMeanGuardStrategy()
    bars=sweep_history()
    old,new=parent.generate(bars),candidate.generate(bars)
    assert old.direction==new.direction==1 and old.stop_loss_price==new.stop_loss_price
    bars=sweep_history(True)
    old,new=parent.generate(bars),candidate.generate(bars)
    assert old.direction==-1 and new.direction==0
    assert (new.exit_long,new.exit_short)==(old.exit_long,old.exit_short)


def test_short_guard_accepts_equality_and_above_mean_but_rejects_below():
    candidate=DirectionalSweepMeanGuardStrategy()
    bars=sweep_history(True)
    assert candidate.entry_conditions(bars,175,190)==(False,True)
    assert candidate.entry_conditions(bars,174.9,190)==(False,True)
    assert candidate.entry_conditions(bars,175.1,190)==(False,False)
