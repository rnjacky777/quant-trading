import pytest

from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from tests.test_portfolio_research import Side, config, run, tape


@pytest.mark.parametrize('sleeve,direction,ratio',[
    ('swing',-1,.5),('swing',1,1),('intraday',-1,1),('intraday',1,1)])
def test_cap_changes_only_swing_short_quantity(sleeve, direction, ratio):
    sleeves = [ResearchSleeve(sleeve,Side(direction),config())]
    parent = run(PortfolioResearchEngine(sleeves),tape())
    child = run(PortfolioResearchEngine(sleeves,swing_short_risk_cap=True),tape())
    a,b = parent.trades[0],child.trades[0]
    assert b.quantity == pytest.approx(a.quantity*ratio)
    assert b.planned_risk == pytest.approx(a.planned_risk*ratio)
    assert (b.entry_price,b.exit_price,b.stop_loss_price,b.exit_reason,b.leverage) == (
        a.entry_price,a.exit_price,a.stop_loss_price,a.exit_reason,1)


def test_existing_loss_brake_is_not_halved_twice():
    sleeves = [ResearchSleeve('swing',Side(-1,True),config(holding_hours=1,fee_bps=10))]
    result = run(PortfolioResearchEngine(sleeves,directional_loss_guard=True,swing_short_risk_cap=True),tape(73))
    traces = [a['swing_short_risk_trace'] for a in result.admissions if a['status']=='accepted']
    assert any(t['loss_brake']==.5 for t in traces)
    assert all(t['sizing_multiplier']==.5 for t in traces)


def test_non_boolean_cap_rejected():
    with pytest.raises(ValueError,match='swing_short_risk_cap'):
        PortfolioResearchEngine([ResearchSleeve('swing',Side(-1),config())],swing_short_risk_cap=1)
