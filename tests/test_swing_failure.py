from dataclasses import replace

import pytest

from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.data.models import MarkPriceCandle, FundingRate
from app.strategies.swing_failure import breakout_boundary, breakout_failed
from tests.test_portfolio_research import Side, config, tape


@pytest.mark.parametrize('direction',[1,-1])
def test_boundary_excludes_breakout_confirmation_and_future_and_requires_close(direction):
    bars=tape(88)
    bars[-8:]=[replace(c,high=150,low=50) for c in bars[-8:]]
    boundary=breakout_boundary(bars,direction)
    assert boundary==100
    close=99 if direction==1 else 101
    assert breakout_failed(bars[:-1]+[replace(bars[-1],close=close)],direction,boundary)
    assert not breakout_failed(bars,direction,boundary)  # Equal, despite wick crossing.
    assert not breakout_failed(bars[:-1]+[replace(bars[-1],timestamp_ms=86*3600000,close=close)],direction,boundary)
    assert breakout_boundary((bars+[replace(bars[-1],high=999)])[:-1],direction)==boundary


@pytest.mark.parametrize('direction',[1,-1])
def test_failure_exits_next_open_and_never_rewrites_each_lot_boundary(direction):
    class Entry(Side):
        def generate(self,history):
            return super().generate(history) if len(history) in (88,92) else Side(0).generate(history)
        def __init__(self):
            super().__init__(direction,True)
    bars=tape(101)
    # First lot boundary100; second lot boundary105(long) or95(short).
    boundary2=105 if direction==1 else 95
    # 4h bar at80 is breakout for first and reference for second.
    bars[80:84]=[replace(c,high=105 if direction==1 else 100,low=95 if direction==-1 else 100) for c in bars[80:84]]
    inside=102 if direction==1 else 98
    bars[95]=replace(bars[95],high=max(inside,100),low=min(inside,100),close=inside)
    bars[96]=replace(bars[96],open=inside,high=max(inside,100),low=min(inside,100))
    bars[99]=replace(bars[99],close=99 if direction==1 else 101,high=101,low=99)
    marks=[MarkPriceCandle(c.exchange,c.symbol,c.timestamp_ms,c.open,c.high,c.low,c.close,timeframe='1h') for c in bars[88:]]
    funding=[FundingRate('test','BTC/USDT',i*3600000,0,100) for i in (88,96)]
    result=PortfolioResearchEngine([ResearchSleeve('swing',Entry(),config(holding_hours=168))],
                                  swing_failure_exit=True).run(bars,evaluation_start_ms=88*3600000,marks=marks,funding=funding)
    trades=sorted(result.trades,key=lambda t:t.entry_timestamp_ms)
    assert len(trades)==2
    assert [a['breakout_level'] for a in result.admissions if a['status']=='accepted']==[100,boundary2]
    assert trades[1].exit_reason=='breakout_failure' and trades[1].exit_timestamp_ms==96*3600000
    assert trades[0].exit_reason=='breakout_failure' and trades[0].exit_timestamp_ms==100*3600000
