from dataclasses import asdict

import pytest

from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.portfolio.research_risk import PortfolioLimits, PortfolioUsage
from scripts.diagnose_admission_risk import decompose
from tests.test_portfolio_research import Side, config, run, tape


def event(side=1, mark=120, costs=False):
    stop = 90 if side==1 else 110
    fee = 10 if costs else 0
    reserve = .001 if costs else 0
    risk = max(side*(mark-stop),0) + stop*fee/10000 + mark*reserve
    return dict(mark=mark,equity=1000,cash=1000,limits=asdict(PortfolioLimits()),
        usage=asdict(PortfolioUsage(gross=mark,margin=100,open_stop_risk=risk)),
        proposal=dict(quantity=1,entry_price=mark,margin=mark,entry_fee=0,planned_risk=5),
        lots=[dict(position_id='one',sleeve='swing',position=dict(quantity=1,direction=side,
                   stop=stop,entry_price=100),config=dict(slippage_bps=0,fee_bps=fee,funding_reserve=reserve))])


@pytest.mark.parametrize('side,mark',[(1,120),(-1,80)])
def test_profit_giveback_is_separate_from_entry_downside(side,mark):
    result=decompose(event(side,mark))
    assert result['remaining_entry_downside']==10
    assert result['giveback']==20
    assert result['future_costs']==0
    # Excluding giveback still leaves the existing 1% budget fully occupied.
    assert result['local_no_giveback_fraction']==0


@pytest.mark.parametrize('side,mark',[(1,95),(-1,105)])
def test_underwater_lot_does_not_count_already_incurred_loss_again(side,mark):
    result=decompose(event(side,mark))
    assert result['remaining_entry_downside']==5
    assert result['giveback']==0
    assert result['local_no_giveback_fraction']==1


def test_future_cost_reserve_remains_and_mismatch_fails():
    e=event(costs=True)
    result=decompose(e)
    assert result['future_costs']==pytest.approx(.09+.12)
    e['usage']['open_stop_risk']+=1
    with pytest.raises(ValueError,match='reconcile'):
        decompose(e)


def test_opposite_lots_do_not_offset_risk():
    e=event(mark=100)
    e['lots']+=event(-1,100)['lots']
    e['usage'].update(gross=200,net=0,margin=200,open_stop_risk=20)
    result=decompose(e)
    assert result['remaining_entry_downside']==20
    assert result['giveback']==0


def test_observer_sees_pre_admission_book_and_cannot_mutate_engine():
    engine=PortfolioResearchEngine([ResearchSleeve('swing',Side(1,True),config(holding_hours=168))])
    expected=run(engine,tape(49))
    seen=[]
    def mutate(snapshot):
        seen.append((len(snapshot['lots']),snapshot['fraction']))
        snapshot['proposal']['quantity']=999999
        snapshot['limits']['daily_entries']=9999
        for lot in snapshot['lots']:
            lot['position']['stop']=999999
        snapshot['lots'].clear()
    actual=run(engine,tape(49),admission_observer=mutate)
    assert actual==expected
    assert seen[0][0]==0 and seen[1][0]==1
    assert any(fraction==0 for _,fraction in seen)
