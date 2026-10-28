"""Isolated USDT perpetual research; never used for order execution.

Historical margin brackets are unverified: flat MMR is an explicit assumption.
Hourly extreme paths and funding ordering cannot reproduce tick-level execution.
"""
from dataclasses import dataclass
from math import isfinite
from typing import Protocol

from app.backtest.metrics import calculate_metrics
from app.backtest.models import BacktestResult, EquityPoint, Trade
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.risk.regime import loss_streak_multiplier
from app.risk.sizing import minimum_required_leverage
from app.strategies.directional_intraday import DirectionalSignal
from app.strategies.base import Action


class DirectionalStrategy(Protocol):
    name: str
    def generate(self, candles: list[Candle]) -> DirectionalSignal: ...


@dataclass(frozen=True)
class PerpetualResearchConfig:
    mode: str = "both"
    initial_cash: float = 10000
    risk_per_trade: float = .0025
    max_exposure: float = .5
    maximum_leverage: int = 2
    fee_bps: float = 10
    slippage_bps: float = 5
    funding_reserve: float = .001
    assumed_mmr: float = .02
    liquidation_fee_bps: float = 50
    daily_entries: int = 2
    holding_hours: int = 24
    loss_brake: bool = True

    def __post_init__(self) -> None:
        if self.mode not in {"both","long_only","short_only"}:
            raise ValueError("invalid direction mode")
        values=(self.initial_cash,self.risk_per_trade,self.max_exposure,self.fee_bps,
                self.slippage_bps,self.funding_reserve,self.assumed_mmr,self.liquidation_fee_bps)
        if not all(isfinite(x) for x in values):
            raise ValueError("research inputs must be finite")
        if self.initial_cash<=0 or not 0<self.risk_per_trade<=.01 or not 0<self.max_exposure<=2:
            raise ValueError("invalid research risk limits")
        if type(self.maximum_leverage) is not int or not 1<=self.maximum_leverage<=2:
            raise ValueError("research leverage limit is 2x")
        if not 0<=self.fee_bps<10000 or not 0<=self.slippage_bps<10000 or not 0<=self.funding_reserve<1:
            raise ValueError("invalid research costs")
        if not 0<self.assumed_mmr<1 or not 0<=self.liquidation_fee_bps<10000:
            raise ValueError("invalid margin assumptions")
        if any(type(x) is not int or x<1 for x in (self.daily_entries,self.holding_hours)):
            raise ValueError("invalid execution limits")


@dataclass
class ResearchPosition:
    direction: int
    entry_timestamp_ms: int
    entry_price: float
    quantity: float
    stop: float
    margin: float
    leverage: int
    entry_fee: float
    entry_slippage: float
    equity_before: float
    planned_risk: float
    funding: float = 0


@dataclass(frozen=True)
class DirectionalTrade(Trade):
    direction: int = 1
    equity_before_entry: float = 0
    entry_notional: float = 0
    leverage_reason: str = ""


def funding_cashflow(position: ResearchPosition, rate: FundingRate) -> float:
    return -position.direction*position.quantity*rate.mark_price*rate.rate


def liquidation_price(position: ResearchPosition, mmr: float) -> float:
    q, entry = position.quantity, position.entry_price
    if position.direction==1:
        return max(0,(q*entry-position.margin-position.funding)/(q*(1-mmr)))
    return (q*entry+position.margin+position.funding)/(q*(1+mmr))


class LongShortResearchEngine:
    def __init__(self, config: PerpetualResearchConfig) -> None:
        self.config=config

    def _open(self, equity: float, candle: Candle, signal: DirectionalSignal,
              multiplier: float) -> tuple[float, ResearchPosition | None]:
        d=signal.direction
        if d not in {-1,1} or signal.stop_loss_price is None or equity<=0:
            return equity,None
        fee,slip=self.config.fee_bps/10000,self.config.slippage_bps/10000
        entry=candle.open*(1+d*slip)
        stop=signal.stop_loss_price
        if d*(entry-stop)<=0:
            return equity,None
        stop_fill=stop*(1-d*slip)
        unit_loss=d*(entry-stop_fill)+fee*(entry+stop_fill)+entry*self.config.funding_reserve
        quantity=min(equity*self.config.risk_per_trade*multiplier/unit_loss,
                     equity*self.config.max_exposure/entry)
        notional=quantity*entry
        leverage=minimum_required_leverage(notional=notional,equity=equity,maximum=self.config.maximum_leverage)
        entry_fee=notional*fee
        if notional/leverage+entry_fee>equity:
            quantity=equity/(entry/leverage+entry*fee)
            notional=quantity*entry
            entry_fee=notional*fee
        return equity-entry_fee,ResearchPosition(d,candle.timestamp_ms,entry,quantity,stop,
            notional/leverage,leverage,entry_fee,quantity*abs(entry-candle.open),equity,quantity*unit_loss)

    def _close(self, cash: float, position: ResearchPosition, candle: Candle,
               reference: float, reason: str) -> tuple[float, DirectionalTrade]:
        d=position.direction
        fill=reference*(1-d*self.config.slippage_bps/10000)
        exit_fee=position.quantity*fill*self.config.fee_bps/10000
        liquid_fee=position.quantity*fill*self.config.liquidation_fee_bps/10000 if reason=="liquidation" else 0
        price_pnl=d*position.quantity*(fill-position.entry_price)
        net=price_pnl-position.entry_fee-exit_fee-liquid_fee+position.funding
        return cash+price_pnl-exit_fee-liquid_fee,DirectionalTrade(
            position.entry_timestamp_ms,candle.timestamp_ms,position.entry_price,fill,position.quantity,
            net,net/(position.margin+position.entry_fee),position.entry_fee+exit_fee,
            position.entry_slippage+position.quantity*abs(fill-reference),reason,position.stop,None,
            position.leverage,position.funding,liquid_fee,position.planned_risk,
            direction=d,equity_before_entry=position.equity_before,entry_notional=position.quantity*position.entry_price,
            leverage_reason="Risk/stop/cost derived quantity, then minimum collateral leverage; trend strength is not a win probability.")

    def validate_inputs(self, candles: list[Candle], *, evaluation_start_ms: int,
            marks: list[MarkPriceCandle], funding: list[FundingRate]) -> int:
        if len(candles)<2 or any(c.timeframe!="1h" for c in candles):
            raise ValueError("hourly perpetual tape required")
        identity=(candles[0].exchange,candles[0].symbol)
        if any((c.exchange,c.symbol)!=identity for c in candles) or any(b.timestamp_ms-a.timestamp_ms!=3600000 for a,b in zip(candles,candles[1:])):
            raise ValueError("invalid or gapped perpetual tape")
        start=next((i for i,c in enumerate(candles) if c.timestamp_ms==evaluation_start_ms),None)
        if start is None or start<1:
            raise ValueError("evaluation start and warmup required")
        expected=[c.timestamp_ms for c in candles[start:]]
        if [m.timestamp_ms for m in marks]!=expected or any((m.exchange,m.symbol)!=identity or m.timeframe!="1h" for m in marks):
            raise ValueError("complete matching hourly marks required")
        schedule=list(range(((evaluation_start_ms+28799999)//28800000)*28800000,candles[-1].timestamp_ms+3600000,28800000))
        if len(funding)!=len(schedule) or any(abs(f.timestamp_ms-t)>1000 or (f.exchange,f.symbol)!=identity for f,t in zip(funding,schedule)):
            raise ValueError("complete actual funding schedule required")
        return start

    def run(self, candles: list[Candle], strategy: DirectionalStrategy, *, evaluation_start_ms: int,
            marks: list[MarkPriceCandle], funding: list[FundingRate]) -> BacktestResult:
        start=self.validate_inputs(candles,evaluation_start_ms=evaluation_start_ms,marks=marks,funding=funding)
        funding_by_hour: dict[int,list[FundingRate]]={}
        for event in funding:
            funding_by_hour.setdefault(event.timestamp_ms//3600000,[]).append(event)
        cash=self.config.initial_cash
        position=None
        trades: list[DirectionalTrade]=[]
        counts: dict[int,int]={}
        curve=[EquityPoint(evaluation_start_ms-3600000,cash,False)]
        max_ratio=0.0
        for i in range(start,len(candles)):
            candle,mark=candles[i],marks[i-start]
            signal=strategy.generate(candles[:i])
            if signal.symbol!=candle.symbol or int(signal.timestamp.timestamp()*1000)!=candles[i-1].timestamp_ms:
                raise ValueError("signal must reference the last completed hourly candle")
            if signal.direction not in {-1,0,1}:
                raise ValueError("invalid signal direction")
            expected_action={1:Action.BUY,-1:Action.SELL,0:Action.HOLD}[signal.direction]
            if signal.action is not expected_action:
                raise ValueError("signal action and direction disagree")
            exited=False
            # Funding exactly at the open belongs to the old position. Events
            # later within the hour belong to the position after open actions.
            events=funding_by_hour.get(candle.timestamp_ms//3600000,[])
            if position is not None:
                for event in events:
                    if event.timestamp_ms<=candle.timestamp_ms:
                        amount=funding_cashflow(position,event);cash+=amount;position.funding+=amount
                timed=candle.timestamp_ms-position.entry_timestamp_ms>=self.config.holding_hours*3600000
                exit_signal=signal.exit_long if position.direction==1 else signal.exit_short
                if timed or exit_signal:
                    cash,trade=self._close(cash,position,candle,candle.open,"time_limit" if timed else "signal")
                    trades.append(trade);position=None;exited=True
            permitted=signal.direction!=0 and (self.config.mode=="both" or
                self.config.mode=="long_only" and signal.direction==1 or self.config.mode=="short_only" and signal.direction==-1)
            day=candle.timestamp_ms//86400000
            if position is None and not exited and permitted and counts.get(day,0)<self.config.daily_entries:
                multiplier=loss_streak_multiplier([t.pnl for t in trades]) if self.config.loss_brake else 1
                cash,position=self._open(cash,candle,signal,multiplier)
                if position is not None:
                    counts[day]=counts.get(day,0)+1
            if position is not None:
                for event in events:
                    if event.timestamp_ms>candle.timestamp_ms:
                        amount=funding_cashflow(position,event);cash+=amount;position.funding+=amount
                adverse=mark.low if position.direction==1 else mark.high
                balance=position.margin+position.direction*position.quantity*(adverse-position.entry_price)+position.funding
                maintenance=position.quantity*adverse*self.config.assumed_mmr
                max_ratio=max(max_ratio,maintenance/balance if balance>0 else 1.0)
                if balance<=maintenance:
                    level=liquidation_price(position,self.config.assumed_mmr)
                    reference=min(mark.open,level) if position.direction==1 else max(mark.open,level)
                    cash,trade=self._close(cash,position,candle,reference,"liquidation")
                    trades.append(trade);position=None
                elif (position.direction==1 and candle.low<=position.stop) or (position.direction==-1 and candle.high>=position.stop):
                    reference=min(candle.open,position.stop) if position.direction==1 else max(candle.open,position.stop)
                    cash,trade=self._close(cash,position,candle,reference,"stop_loss")
                    trades.append(trade);position=None
            if i==len(candles)-1 and position is not None:
                cash,trade=self._close(cash,position,candle,candle.close,"end_of_data")
                trades.append(trade);position=None
            equity=cash+(position.direction*position.quantity*(mark.close-position.entry_price) if position else 0)
            if equity<=0 or not isfinite(equity):
                raise ValueError("research account insolvent; scenario failed")
            curve.append(EquityPoint(candle.timestamp_ms,equity,position is not None))
        if abs(cash-self.config.initial_cash-sum(t.pnl for t in trades))>1e-6:
            raise ValueError("derivative cash/PnL reconciliation failed")
        metrics=calculate_metrics(curve,trades,self.config.initial_cash,"1h",max_ratio)
        return BacktestResult(strategy.name,candles[0].symbol,"1h",self.config.initial_cash,cash,metrics,trades,curve)
