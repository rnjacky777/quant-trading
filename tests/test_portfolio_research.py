from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.data.aggregation import completed_four_hour_bars
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.portfolio.research_risk import PortfolioLimits, PortfolioUsage, RiskLot, admission_fraction, portfolio_usage
from app.strategies.base import Action
from app.strategies.directional_intraday import DirectionalSignal
from app.strategies.directional_swing import DirectionalSwingStrategy


def tape(n=4):
    return [Candle("test","BTC/USDT","1h",i*3600000,100,100,100,100,1) for i in range(n)]


class Side:
    name="test_side"
    def __init__(self,direction,always=False):
        self.direction,self.always=direction,always
    def generate(self,candles):
        d=self.direction if self.always or len(candles)==1 else 0
        return DirectionalSignal("BTC/USDT",datetime.fromtimestamp(candles[-1].timestamp_ms/1000,timezone.utc),
            Action.BUY if d==1 else Action.SELL if d==-1 else Action.HOLD,1 if d else 0,self.name,
            stop_loss_price=80 if d==1 else 120 if d==-1 else None,direction=d)


def run(engine,bars,**kwargs):
    marks=[MarkPriceCandle(c.exchange,c.symbol,c.timestamp_ms,c.open,c.high,c.low,c.close,timeframe="1h") for c in bars[1:]]
    funding=[FundingRate("test","BTC/USDT",i*3600000,0,100) for i in range(8,len(bars),8)]
    return engine.run(bars,evaluation_start_ms=3600000,marks=marks,funding=funding,**kwargs)


def config(**kwargs):
    return replace(PerpetualResearchConfig(fee_bps=0,slippage_bps=0,funding_reserve=0),**kwargs)


def test_opposite_lots_share_one_cash_account_and_exit_independently():
    engine=PortfolioResearchEngine([
        ResearchSleeve("intraday",Side(-1),config(holding_hours=1)),
        ResearchSleeve("swing",Side(1),config(holding_hours=168)),
    ])
    result=run(engine,tape())
    assert result.initial_cash==10000 and result.final_equity==10000
    assert max(p.open_positions for p in result.portfolio_curve)==2
    short,long=result.trades
    assert short.sleeve=="intraday" and short.exit_reason=="time_limit"
    assert short.exit_timestamp_ms==2*3600000
    assert long.sleeve=="swing" and long.exit_reason=="end_of_data"
    assert len({t.position_id for t in result.trades})==2
    assert run(engine,tape())==result


def test_same_sleeve_can_hold_four_lots_without_a_position_count_cap():
    engine=PortfolioResearchEngine([ResearchSleeve("swing",Side(1,True),config(holding_hours=168))])
    result=run(engine,tape(49))
    assert max(p.open_positions for p in result.portfolio_curve)==4
    assert len(result.trades)==4
    assert Counter(t.entry_timestamp_ms//86400000 for t in result.trades)=={0:2,1:2}
    assert len({t.position_id for t in result.trades})==4
    assert any(a['status']=='rejected' and a['reason']=='open_stop_risk' for a in result.admissions)


def test_gross_not_net_exposure_controls_hedged_positions():
    usage=portfolio_usage([RiskLot(1,1,80,100,0,0,0),RiskLot(1,-1,120,100,0,0,0)],100)
    assert usage.gross==200 and usage.net==0 and usage.open_stop_risk==40
    fraction,_=admission_fraction(equity=1000,cash=1000,usage=PortfolioUsage(gross=500),
        notional=100,margin_and_fee=100,planned_risk=1,limits=PortfolioLimits())
    assert fraction==0
    engine=PortfolioResearchEngine([ResearchSleeve("a",Side(1),config()),ResearchSleeve("b",Side(-1),config())],
        PortfolioLimits(max_gross_exposure=.01))
    result=run(engine,tape())
    assert len(result.trades)==1
    assert any(a['reason']=='gross_exposure' and a['status']=='rejected' for a in result.admissions)


def test_reserved_margin_is_not_reused_by_the_second_sleeve():
    engine=PortfolioResearchEngine([ResearchSleeve("a",Side(1),config()),ResearchSleeve("b",Side(-1),config())],
        PortfolioLimits(max_margin_fraction=.02))
    result=run(engine,tape())
    assert len(result.trades)==2
    assert max(p.reserved_margin for p in result.portfolio_curve)==pytest.approx(200)
    assert result.final_equity==10000
    assert result.admissions[1]['scale']<1
    assert result.admissions[1]['reason']=='available_collateral'


def test_both_lots_pay_costs_even_when_net_position_is_zero():
    cfg=config(fee_bps=10,slippage_bps=5)
    result=run(PortfolioResearchEngine([ResearchSleeve("a",Side(1),cfg),ResearchSleeve("b",Side(-1),cfg)]),tape())
    assert result.final_equity<10000
    assert all(t.fees>0 and t.slippage_cost>0 for t in result.trades)
    assert result.final_equity==pytest.approx(10000+sum(t.pnl for t in result.trades))


def test_received_funding_remains_reserved_in_the_position_wallet():
    bars=tape(10)
    engine=PortfolioResearchEngine([ResearchSleeve("swing",Side(-1),config(holding_hours=168))])
    marks=[MarkPriceCandle(c.exchange,c.symbol,c.timestamp_ms,c.open,c.high,c.low,c.close,timeframe="1h") for c in bars[1:]]
    result=engine.run(bars,evaluation_start_ms=3600000,marks=marks,
        funding=[FundingRate("test","BTC/USDT",8*3600000+1,.001,100)])
    before=next(p for p in result.portfolio_curve if p.timestamp_ms==7*3600000)
    after=next(p for p in result.portfolio_curve if p.timestamp_ms==8*3600000)
    assert after.cash>before.cash and after.reserved_margin>before.reserved_margin
    assert after.cash-after.reserved_margin==pytest.approx(before.cash-before.reserved_margin)


def test_complete_4h_aggregation_excludes_unfinished_bucket():
    bars=tape(7)
    grouped=completed_four_hour_bars(bars)
    assert len(grouped)==1 and grouped[0].timestamp_ms==0
    bars[-1]=replace(bars[-1],close=500,high=500)
    assert completed_four_hour_bars(bars)==grouped
    with pytest.raises(ValueError):
        PortfolioResearchEngine([ResearchSleeve("same",Side(1),config()),ResearchSleeve("same",Side(-1),config())])


def test_swing_only_opens_after_completed_four_hour_bucket():
    bars=tape(244)
    bars[-1]=replace(bars[-1],open=199,high=201,low=198,close=200)
    strategy=DirectionalSwingStrategy()
    assert strategy.generate(bars[:-1]).direction==0
    completed=strategy.generate(bars)
    assert completed.direction==1 and completed.stop_loss_price<200
    partial=replace(bars[-1],timestamp_ms=244*3600000,open=1000,high=1000,low=1000,close=1000)
    assert strategy.generate(bars+[partial]).direction==0
    assert strategy.generate((bars+[partial])[:-1])==completed


def test_same_direction_decay_reduces_additions_without_banning_multiple_lots():
    engine=PortfolioResearchEngine([ResearchSleeve("swing",Side(1,True),config(holding_hours=168))],
        PortfolioLimits(same_direction_risk_decay=True))
    result=run(engine,tape(49))
    assert result.maximum_concurrent_positions==5
    accepted=[a for a in result.admissions if a['status']=='accepted']
    for n,a in enumerate(accepted):
        assert a['same_direction_before']==n
        assert a['planned_risk']/a['equity_before']==pytest.approx(.0025/(1+n))
    opposite=PortfolioResearchEngine([ResearchSleeve("a",Side(1),config()),ResearchSleeve("b",Side(-1),config())],
        PortfolioLimits(same_direction_risk_decay=True))
    result=run(opposite,tape())
    assert all(t.planned_risk/t.equity_before_entry==pytest.approx(.0025) for t in result.trades)


def test_longer_holding_limit_changes_deadline_but_never_delays_signal_or_stop():
    bars=tape(51)
    for hours in (24,48):
        result=run(PortfolioResearchEngine([ResearchSleeve("intraday",Side(1),config(holding_hours=hours))]),bars)
        assert len(result.trades)==1
        assert result.trades[0].exit_timestamp_ms==(1+hours)*3600000
        assert result.trades[0].exit_reason=="time_limit"
    class ExitEarly(Side):
        def generate(self,candles):
            return replace(super().generate(candles),exit_long=len(candles)>=3)
    result=run(PortfolioResearchEngine([ResearchSleeve("intraday",ExitEarly(1),config(holding_hours=48))]),bars)
    assert result.trades[0].exit_timestamp_ms==3*3600000
    assert result.trades[0].exit_reason=="signal"
    bars[3]=replace(bars[3],low=79)
    result=run(PortfolioResearchEngine([ResearchSleeve("intraday",Side(1),config(holding_hours=48))]),bars)
    assert result.trades[0].exit_timestamp_ms==3*3600000
    assert result.trades[0].exit_reason=="stop_loss"


@pytest.mark.parametrize("side",[1,-1])
@pytest.mark.parametrize("gap",[False,True])
def test_swing_protection_activates_after_close_and_gaps_are_not_guaranteed_breakeven(side,gap):
    bars=tape(4)
    bars[1]=replace(bars[1],high=130 if side==1 else 110,low=90 if side==1 else 70,
                    close=120 if side==1 else 80)
    if gap:
        price=95 if side==1 else 105
        bars[2]=replace(bars[2],open=price,high=price+1,low=price-1,close=price)
    else:
        price=110 if side==1 else 90
        bars[2]=replace(bars[2],open=price,high=111 if side==1 else 101,
                        low=99 if side==1 else 89,close=price)
    result=run(PortfolioResearchEngine([ResearchSleeve("swing",Side(side),config(holding_hours=168))],
                                      swing_price_protection=True),bars)
    trade=result.trades[0]
    assert trade.exit_timestamp_ms==2*3600000  # Not the activation bar's earlier adverse wick.
    assert trade.exit_reason=="profit_protection"
    assert trade.stop_loss_price==(80 if side==1 else 120)  # Initial risk is immutable.
    update=result.admissions[0]['stop_updates'][0]
    assert update['decision_timestamp_ms']==3600000 and update['active_from_ms']==7200000
    assert update['to_stop']==100
    assert trade.pnl<0 if gap else trade.pnl==0


@pytest.mark.parametrize("side",[1,-1])
def test_wick_alone_does_not_activate_protection_and_short_horizon_is_unchanged(side):
    bars=tape(4)
    bars[1]=replace(bars[1],high=130 if side==1 else 110,low=90 if side==1 else 70,
                    close=110 if side==1 else 90)
    result=run(PortfolioResearchEngine([ResearchSleeve("swing",Side(side),config(holding_hours=168))],
                                      swing_price_protection=True),bars)
    assert 'stop_updates' not in result.admissions[0]
    assert result.trades[0].exit_reason=="end_of_data"
    bars[1]=replace(bars[1],close=120 if side==1 else 80)
    engine=PortfolioResearchEngine([ResearchSleeve("intraday",Side(side),config())],swing_price_protection=True)
    assert 'stop_updates' not in run(engine,bars).admissions[0]


def test_signal_observer_captures_open_exit_suppression_and_quota_without_changing_book():
    from copy import deepcopy
    events=[]
    def observe(event):
        events.append(deepcopy(event))
        event['outcome']['status']='mutated_copy'
    engine=PortfolioResearchEngine([ResearchSleeve("intraday",Side(1,True),config(holding_hours=1))])
    plain=run(engine,tape(7))
    instrumented=run(engine,tape(7),signal_observer=observe)
    assert instrumented==plain
    assert len(events)==6
    assert Counter(e['outcome']['status'] for e in events)=={'accepted':2,'skipped':2,'rejected':2}
    assert {e['outcome']['reason'] for e in events if e['outcome']['status']=='skipped'}=={'open_exit_cooldown'}
    assert {e['outcome']['reason'] for e in events if e['outcome']['status']=='rejected'}=={'daily_entry_limit'}
    assert all(e['signal_timestamp_ms']==e['timestamp_ms']-3600000 for e in events)


def test_signal_observer_preserves_stop_risk_rejection_and_direction_disabled():
    events=[]
    engine=PortfolioResearchEngine([ResearchSleeve("intraday",Side(1,True),config(holding_hours=168))],
                                   PortfolioLimits(max_open_stop_risk=.0025))
    result=run(engine,tape(4),signal_observer=events.append)
    assert len(result.trades)==1 and len(events)==3
    assert all(e['outcome']['reason']=='open_stop_risk' for e in events[1:])
    events=[]
    engine=PortfolioResearchEngine([ResearchSleeve("intraday",Side(-1,True),config(mode='long_only'))])
    assert not run(engine,tape(4),signal_observer=events.append).trades
    assert len(events)==3 and all(e['outcome']['reason']=='direction_disabled' for e in events)


@pytest.mark.parametrize("side",[1,-1])
def test_directional_guard_keeps_own_losses_braked_after_opposite_win_and_retains_shared_brake(side):
    class Alternating:
        name="directional_guard_test"
        def generate(self,candles):
            d={1:side,3:side,25:-side,27:side}.get(len(candles),0)
            return DirectionalSignal("BTC/USDT",datetime.fromtimestamp(candles[-1].timestamp_ms/1000,timezone.utc),
                Action.BUY if d==1 else Action.SELL if d==-1 else Action.HOLD,1 if d else 0,self.name,
                stop_loss_price=80 if d==1 else 120 if d==-1 else None,direction=d)
    bars=tape(29)  # Two entries per UTC day; the opposite win occurs on day two.
    for index in (2,4,26):
        p=100-side*10
        bars[index]=replace(bars[index],open=p,high=p,low=p,close=p)
    sleeve=ResearchSleeve("intraday",Alternating(),config(holding_hours=1))
    plain=run(PortfolioResearchEngine([sleeve]),bars)
    def mutate_observer_copy(event):
        event['outcome']['loss_guard_trace']['shared_pnls'].clear()
    guarded=run(PortfolioResearchEngine([sleeve],directional_loss_guard=True),bars,signal_observer=mutate_observer_copy)
    assert len(plain.trades)==len(guarded.trades)==4
    assert plain.trades[-1].planned_risk/plain.trades[-1].equity_before_entry==pytest.approx(.0025)
    assert guarded.trades[-1].planned_risk/guarded.trades[-1].equity_before_entry==pytest.approx(.00125)
    third=guarded.admissions[2]['loss_guard_trace']
    assert third['shared_multiplier']==.5 and third['directional_multiplier']==1
    assert third['final_brake_multiplier']==.5
    last=guarded.admissions[3]['loss_guard_trace']
    assert last['shared_multiplier']==1 and last['directional_multiplier']==.5
    assert last['final_brake_multiplier']==.5
    assert len(last['shared_pnls'])==3 and len(last['directional_pnls'])==2
    assert all(a['loss_guard_trace']['final_brake_multiplier']>=.5 for a in guarded.admissions)
    assert all('loss_guard_trace' not in a for a in plain.admissions)


def test_directional_loss_guard_uses_minimum_not_compounded_brake_and_keeps_zero_semantics():
    from app.risk.regime import directional_loss_guard_multiplier
    assert directional_loss_guard_multiplier([-1,-1,2],[-1,-1])==.5
    assert directional_loss_guard_multiplier([-1,-1],[2])==.5
    assert directional_loss_guard_multiplier([-1,-1],[-1,-1])==.5
    assert directional_loss_guard_multiplier([2,0],[-1,0,-1])==.5
    assert directional_loss_guard_multiplier([2],[2])==1
