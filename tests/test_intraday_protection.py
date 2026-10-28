from dataclasses import replace

import pytest

from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from tests.test_portfolio_research import Side, config, run, tape


@pytest.mark.parametrize('side',[1,-1])
@pytest.mark.parametrize('gap',[False,True])
def test_intraday_protection_uses_completed_close_and_next_hour_stop(side,gap):
    bars=tape(4)
    price=120 if side==1 else 80
    # Adverse wick does not hit initial stop; close alone activates.
    bars[1]=replace(bars[1],high=max(110,price),low=min(90,price),close=price)
    opening=(95 if side==1 else 105) if gap else 100
    bars[2]=replace(bars[2],open=opening,high=max(opening,101),low=min(opening,99),close=opening)
    cfg=config(fee_bps=10,slippage_bps=0)
    result=run(PortfolioResearchEngine([ResearchSleeve('intraday',Side(side),cfg)],intraday_price_protection=True),bars)
    t=result.trades[0];u=result.admissions[0]['stop_updates'][0]
    assert u['decision_timestamp_ms']==3600000 and u['active_from_ms']==7200000
    assert u['to_stop']==100 and t.stop_loss_price==(80 if side==1 else 120)
    assert t.exit_reason=='profit_protection' and t.exit_timestamp_ms==7200000
    assert t.exit_price==opening and t.pnl<0  # Price protection still pays costs.


@pytest.mark.parametrize('side',[1,-1])
def test_wick_or_initial_stop_prevents_retroactive_protection_and_swing_is_unchanged(side):
    bars=tape(4)
    bars[1]=replace(bars[1],high=130 if side==1 else 110,low=90 if side==1 else 70,
                    close=110 if side==1 else 90)
    engine=PortfolioResearchEngine([ResearchSleeve('intraday',Side(side),config())],intraday_price_protection=True)
    assert 'stop_updates' not in run(engine,bars).admissions[0]
    bars[1]=replace(bars[1],high=130,low=70,close=120 if side==1 else 80)
    stopped=run(engine,bars)
    assert stopped.trades[0].exit_reason=='stop_loss' and 'stop_updates' not in stopped.admissions[0]
    wave=PortfolioResearchEngine([ResearchSleeve('swing',Side(side),config())],intraday_price_protection=True)
    bars[1]=replace(bars[1],high=125 if side==1 else 110,low=90 if side==1 else 75)
    assert 'stop_updates' not in run(wave,bars).admissions[0]
