from collections import Counter
from datetime import datetime, timezone
from dataclasses import replace

import pytest

from app.backtest.long_short_research import (LongShortResearchEngine, PerpetualResearchConfig,
    ResearchPosition, funding_cashflow, liquidation_price)
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.strategies.base import Action
from app.strategies.directional_intraday import DirectionalIntradayStrategy, DirectionalSignal


def bars(prices):
    return [Candle("test","BTC/USDT","1h",i*3600000,p,p,p,p,1) for i,p in enumerate(prices)]


def marks(tape):
    return [MarkPriceCandle(c.exchange,c.symbol,c.timestamp_ms,c.open,c.high,c.low,c.close,timeframe="1h") for c in tape[1:]]


class FixedSide:
    name="test_directional"
    def __init__(self, direction, always=False):
        self.direction,self.always=direction,always
    def generate(self, tape):
        d=self.direction if self.always or len(tape)==1 else 0
        stop=tape[-1].close*(1-.2*d) if d else None
        return DirectionalSignal("BTC/USDT",datetime.fromtimestamp(tape[-1].timestamp_ms/1000,timezone.utc),
            Action.BUY if d==1 else Action.SELL if d==-1 else Action.HOLD,1 if d else 0,self.name,
            stop_loss_price=stop,direction=d)


@pytest.mark.parametrize("direction,expected", [(-1,12.5),(1,-12.5)])
def test_directional_pnl_reconciles_and_margin_is_not_spent(direction,expected):
    tape=bars([100,100,90])
    config=PerpetualResearchConfig(fee_bps=0,slippage_bps=0,funding_reserve=0)
    result=LongShortResearchEngine(config).run(tape,FixedSide(direction),evaluation_start_ms=3600000,marks=marks(tape),funding=[])
    assert result.trades[0].pnl==pytest.approx(expected)
    assert result.final_equity==pytest.approx(10000+expected)
    assert result.trades[0].direction==direction
    assert result.trades[0].leverage==1


@pytest.mark.parametrize("direction", [-1,1])
def test_positive_funding_charges_longs_and_pays_shorts(direction):
    tape=bars([100]*10)
    config=PerpetualResearchConfig(fee_bps=0,slippage_bps=0,funding_reserve=0)
    funding=[FundingRate("test","BTC/USDT",8*3600000+1,.001,100)]
    result=LongShortResearchEngine(config).run(tape,FixedSide(direction),evaluation_start_ms=3600000,marks=marks(tape),funding=funding)
    assert result.trades[0].funding==pytest.approx(-direction*.125)
    assert result.final_equity==pytest.approx(10000-direction*.125)
    position=ResearchPosition(direction,0,100,1,80 if direction==1 else 120,50,2,0,0,1000,20)
    assert funding_cashflow(position,replace(funding[0],rate=-.001))==pytest.approx(direction*.1)


@pytest.mark.parametrize("direction", [-1,1])
def test_roundtrip_slippage_and_fees_are_adverse_for_both_sides(direction):
    tape=bars([100,100,100])
    result=LongShortResearchEngine(PerpetualResearchConfig(funding_reserve=0)).run(
        tape,FixedSide(direction),evaluation_start_ms=3600000,marks=marks(tape),funding=[])
    trade=result.trades[0]
    assert trade.pnl==pytest.approx(-trade.fees-trade.slippage_cost)
    assert trade.pnl<0


def test_short_gap_stop_exceeds_planned_risk_and_liquidation_is_directional():
    tape=bars([100,100,130])
    result=LongShortResearchEngine(PerpetualResearchConfig(fee_bps=0,slippage_bps=0,funding_reserve=0)).run(
        tape,FixedSide(-1),evaluation_start_ms=3600000,marks=marks(tape),funding=[])
    assert result.trades[0].exit_reason=="stop_loss"
    assert result.trades[0].exit_price==130
    assert -result.trades[0].pnl>result.trades[0].planned_risk
    short=ResearchPosition(-1,0,100,1,120,50,2,0,0,1000,20)
    long=replace(short,direction=1,stop=80)
    assert liquidation_price(short,.02)==pytest.approx(150/1.02)
    assert liquidation_price(long,.02)==pytest.approx(50/.98)


def test_short_adverse_mark_can_liquidate_before_trade_price_stop():
    tape=bars([100,100,100])
    mark=marks(tape)
    mark[0]=replace(mark[0],high=250)
    result=LongShortResearchEngine(PerpetualResearchConfig(fee_bps=0,slippage_bps=0,funding_reserve=0)).run(
        tape,FixedSide(-1),evaluation_start_ms=3600000,marks=mark,funding=[])
    assert result.trades[0].exit_reason=="liquidation"
    assert result.metrics.liquidation_count==1
    assert result.trades[0].liquidation_fee>0


def test_missing_derivative_inputs_are_rejected_and_modes_do_not_open_wrong_side():
    tape=bars([100,100,90])
    engine=LongShortResearchEngine(PerpetualResearchConfig(mode="long_only"))
    result=engine.run(tape,FixedSide(-1),evaluation_start_ms=3600000,marks=marks(tape),funding=[])
    assert result.trades==[]
    with pytest.raises(ValueError,match="marks"):
        engine.run(tape,FixedSide(-1),evaluation_start_ms=3600000,marks=[],funding=[])
    tape=bars([100]*10)
    with pytest.raises(ValueError,match="funding"):
        engine.run(tape,FixedSide(-1),evaluation_start_ms=3600000,marks=marks(tape),funding=[])


def test_real_strategy_short_signal_is_symmetric_and_only_uses_completed_history():
    tape=bars([200-i*.1 for i in range(243)])
    tape[-1]=replace(tape[-1],open=101,high=102,low=99,close=100)
    strategy=DirectionalIntradayStrategy()
    signal=strategy.generate(tape)
    assert signal.direction==-1
    assert signal.action is Action.SELL
    assert signal.stop_loss_price>tape[-1].close
    future=replace(tape[-1],timestamp_ms=tape[-1].timestamp_ms+3600000,open=300,high=300,low=300,close=300)
    assert strategy.generate((tape+[future])[:-1])==signal


def test_short_daily_cap_time_exit_and_repeated_run_state():
    class Stops(FixedSide):
        def generate(self,tape):
            return replace(super().generate(tape),stop_loss_price=105)
    tape=[replace(c,high=106) for c in bars([100]*49)]
    funding=[FundingRate("test","BTC/USDT",i*3600000,0,100) for i in range(8,49,8)]
    engine=LongShortResearchEngine(PerpetualResearchConfig(fee_bps=0,slippage_bps=0,funding_reserve=0))
    result=engine.run(tape,Stops(-1,True),evaluation_start_ms=3600000,marks=marks(tape),funding=funding)
    assert Counter(t.entry_timestamp_ms//86400000 for t in result.trades)=={0:2,1:2,2:1}
    assert engine.run(tape,Stops(-1,True),evaluation_start_ms=3600000,marks=marks(tape),funding=funding)==result
    tape=bars([100]*10)
    engine=LongShortResearchEngine(PerpetualResearchConfig(holding_hours=3))
    result=engine.run(tape,FixedSide(-1,True),evaluation_start_ms=3600000,marks=marks(tape),
        funding=[FundingRate("test","BTC/USDT",8*3600000,0,100)])
    assert result.trades[0].exit_reason=="time_limit"
    assert result.trades[0].exit_timestamp_ms==4*3600000
    assert result.trades[1].entry_timestamp_ms==5*3600000
