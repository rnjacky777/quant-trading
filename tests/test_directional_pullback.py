from dataclasses import replace

import pytest

from app.data.models import Candle
from app.strategies.directional_pullback import DirectionalPullbackStrategy


def history(short):
    bars=[Candle("test","BTC/USDT","1h",i*3600000,100+i*.1,102+i*.1,98+i*.1,100+i*.1,1) for i in range(244)]
    bars[-2]=replace(bars[-2],open=119,high=120,low=117,close=118)
    bars[-1]=replace(bars[-1],open=123,high=124.2,low=122.8,close=124)
    if short:
        bars=[replace(c,open=250-c.open,high=250-c.low,low=250-c.high,close=250-c.close) for c in bars]
    return bars


@pytest.mark.parametrize("short",[False,True])
def test_completed_reclaim_is_symmetric_and_not_repeated_without_another_cross(short):
    strategy=DirectionalPullbackStrategy(); bars=history(short)
    signal=strategy.generate(bars)
    assert signal.direction==(-1 if short else 1)
    assert strategy.generate(bars[:-1]).direction==0
    next_bar=replace(bars[-1],timestamp_ms=bars[-1].timestamp_ms+3600000)
    assert strategy.generate(bars+[next_bar]).direction==0
    assert strategy.generate((bars+[next_bar])[:-1])==signal
    assert (signal.stop_loss_price>bars[-1].close) if short else (signal.stop_loss_price<bars[-1].close)


def test_touching_mean_is_not_a_reclaim_and_opposite_context_is_rejected():
    strategy=DirectionalPullbackStrategy()
    bars=[Candle("test","BTC/USDT","1h",i*3600000,100,101,99,100,1) for i in range(21)]
    bars[-1]=replace(bars[-1],open=102,high=103,low=102,close=103)
    assert strategy.entry_conditions(bars,2,1)==(False,False)
    assert strategy.entry_conditions(history(False),1,2)==(False,False)
