from dataclasses import replace

import pytest

from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.risk.regime import directional_slope_cap
from tests.test_portfolio_research import Side, config, run, tape


@pytest.mark.parametrize('direction',[1,-1])
def test_completed_four_hour_slope_is_directional_and_ignores_incomplete_bucket(direction):
    bars=[replace(c,open=100+i,high=100+i,low=100+i,close=100+i) for i,c in enumerate(tape(264))]
    assert directional_slope_cap(bars,direction)==(1 if direction==1 else .5)
    assert directional_slope_cap(tape(264),direction)==.5
    assert directional_slope_cap(bars[:263],direction)==.5
    future=replace(bars[-1],timestamp_ms=264*3600000,high=9999,close=9999)
    assert directional_slope_cap(bars+[future],direction)==directional_slope_cap(bars,direction)


@pytest.mark.parametrize('direction',[1,-1])
def test_cap_halves_risk_not_stop_and_does_not_compound_loss_brake(direction):
    # Insufficient history is conservatively capped, independent of future prices.
    sleeve=ResearchSleeve('intraday',Side(direction,True),config(holding_hours=1,fee_bps=10))
    bars=tape(49)
    plain=run(PortfolioResearchEngine([sleeve],directional_loss_guard=True),bars)
    capped=run(PortfolioResearchEngine([sleeve],directional_loss_guard=True,slope_risk_cap=True),bars)
    assert len(plain.trades)==len(capped.trades)
    assert capped.trades[0].quantity==plain.trades[0].quantity/2
    assert capped.trades[0].stop_loss_price==plain.trades[0].stop_loss_price
    assert capped.admissions[0]['slope_risk_trace']['capped_multiplier']==.5
    accepted=[a for a in capped.admissions if a['status']=='accepted']
    assert all(a['slope_risk_trace']['sizing_multiplier']==.5 for a in accepted)
    assert any(a['slope_risk_trace']['loss_brake']==.5 for a in accepted)
    assert all('slope_risk_trace' not in a for a in plain.admissions)
    bars[1]=replace(bars[1],high=1000,close=900)
    changed=run(PortfolioResearchEngine([sleeve],slope_risk_cap=True),bars)
    assert changed.trades[0].quantity==capped.trades[0].quantity
