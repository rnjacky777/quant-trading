from dataclasses import replace

from app.data.models import Candle
from app.strategies.directional_pullback import DirectionalPullbackStrategy
from app.strategies.pullback_reset import DirectionalPullbackResetStrategy


def history(short=True):
    bars=[Candle("test","BTC/USDT","1h",i*3600000,100+i*.1,102+i*.1,98+i*.1,100+i*.1,1) for i in range(244)]
    bars[-2]=replace(bars[-2],open=119,high=120,low=117,close=118)
    bars[-1]=replace(bars[-1],open=123,high=124.2,low=122.8,close=124)
    return [replace(c,open=250-c.open,high=250-c.low,low=250-c.high,close=250-c.close) for c in bars] if short else bars


def append_price(bars, price):
    return bars+[replace(bars[-1],timestamp_ms=bars[-1].timestamp_ms+3600000,
                         open=price+.5,high=price+1,low=price-.2,close=price)]


def test_short_event_consumed_by_signal_and_rearmed_only_by_new_context_cross():
    parent,candidate=DirectionalPullbackStrategy(),DirectionalPullbackResetStrategy()
    first=history()
    initial=candidate.generate(first)
    assert initial.direction==parent.generate(first).direction==-1
    repeated=append_price(append_price(first,128),125)
    assert parent.generate(repeated).direction==-1
    assert candidate.generate(repeated).direction==0
    rearmed=append_price(append_price(repeated,132),124)
    assert candidate.generate(rearmed).direction==-1
    # No fill/position callback is involved; replay and call order do not matter.
    assert candidate.generate(first)==initial
    assert candidate.generate((rearmed+[replace(rearmed[-1],timestamp_ms=rearmed[-1].timestamp_ms+3600000)])[:-1])==candidate.generate(rearmed)


def test_no_observed_context_reset_blocks_short_but_preserves_long_and_exit():
    parent,candidate=DirectionalPullbackStrategy(),DirectionalPullbackResetStrategy()
    bars=history()
    bars[-2]=replace(bars[-2],open=127,high=129,low=127,close=128)
    old,new=parent.generate(bars),candidate.generate(bars)
    assert old.direction==-1 and new.direction==0
    assert (new.exit_long,new.exit_short)==(old.exit_long,old.exit_short)
    long_bars=history(False)
    old,new=parent.generate(long_bars),candidate.generate(long_bars)
    assert new.direction==old.direction==1
    assert new.stop_loss_price==old.stop_loss_price
