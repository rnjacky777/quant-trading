from dataclasses import replace

import pytest

from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.data.models import MarkPriceCandle, FundingRate
from app.strategies.swing_failure import breakout_failed
from tests.test_portfolio_research import Side, config, tape


@pytest.mark.parametrize('direction',[1,-1])
def test_hourly_failure_uses_close_not_wick_or_equality(direction):
    bars=tape(89)
    bars[-1]=replace(bars[-1],high=110,low=90)
    assert not breakout_failed(bars,direction,100,hourly=True)
    bars[-1]=replace(bars[-1],close=100-direction)
    assert breakout_failed(bars,direction,100,hourly=True)
    assert not breakout_failed(bars,direction,100)


@pytest.mark.parametrize('direction',[1,-1])
def test_next_open_execution_and_intraday_unaffected(direction):
    class Entry(Side):
        def generate(self,history):
            return Side(direction,True).generate(history) if len(history)==88 else Side(0).generate(history)
    bars=tape(94)
    bars[88]=replace(bars[88],close=100-direction,low=99,high=101)
    bars[89]=replace(bars[89],open=100-2*direction,low=98,high=102)
    marks=[MarkPriceCandle(c.exchange,c.symbol,c.timestamp_ms,c.open,c.high,c.low,c.close,timeframe='1h') for c in bars[88:]]
    funding=[FundingRate('test','BTC/USDT',88*3600000,0,100)]
    sleeves=[ResearchSleeve(s,Entry(direction),config(holding_hours=168)) for s in ('swing','intraday')]
    result=PortfolioResearchEngine(sleeves,swing_failure_exit=True,swing_hourly_failure=True).run(
        bars,evaluation_start_ms=88*3600000,marks=marks,funding=funding)
    swing=next(t for t in result.trades if t.sleeve=='swing')
    intraday=next(t for t in result.trades if t.sleeve=='intraday')
    assert swing.exit_reason=='breakout_failure'
    assert swing.exit_timestamp_ms==89*3600000 and swing.exit_price==bars[89].open
    assert intraday.exit_timestamp_ms>swing.exit_timestamp_ms


def test_hourly_mode_requires_frozen_boundary_mode():
    with pytest.raises(ValueError,match='swing_hourly_failure'):
        PortfolioResearchEngine([ResearchSleeve('swing',Side(1),config())],swing_hourly_failure=True)
