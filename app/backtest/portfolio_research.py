"""Shared-cash, independent-lot BTC perpetual portfolio research.

No position-count limit: additions are controlled by daily entries, gross
exposure, aggregate stop risk and collateral. Not a live execution adapter.
"""
from dataclasses import asdict, dataclass, field, replace
from math import isfinite
from collections.abc import Callable
from copy import deepcopy

from app.backtest.long_short_research import (DirectionalStrategy, DirectionalTrade,
    LongShortResearchEngine, PerpetualResearchConfig, ResearchPosition, funding_cashflow, liquidation_price)
from app.backtest.metrics import calculate_metrics
from app.backtest.models import BacktestResult, EquityPoint
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.portfolio.research_risk import PortfolioLimits, RiskLot, admission_fraction, portfolio_usage
from app.risk.regime import directional_loss_guard_multiplier, loss_streak_multiplier, directional_slope_cap
from app.strategies.base import Action
from app.strategies.swing_failure import breakout_boundary, breakout_failed

SWING_LONG_SIGNAL_HOLD_HOURS = 72


@dataclass(frozen=True)
class ResearchSleeve:
    name: str
    strategy: DirectionalStrategy
    config: PerpetualResearchConfig


@dataclass
class OpenLot:
    position_id: str
    sleeve: str
    position: ResearchPosition
    initial_stop: float | None = None
    breakout_level: float | None = None


@dataclass(frozen=True)
class PortfolioTrade(DirectionalTrade):
    position_id: str = ""
    sleeve: str = ""


@dataclass(frozen=True)
class PortfolioPoint:
    timestamp_ms: int
    equity: float
    cash: float
    open_positions: int
    gross_exposure: float
    net_exposure: float
    reserved_margin: float
    open_stop_risk: float
    admission_limit_exceeded: bool


@dataclass(frozen=True)
class PortfolioResearchResult(BacktestResult):
    portfolio_curve: list[PortfolioPoint] = field(default_factory=list)
    admissions: list[dict] = field(default_factory=list)
    maximum_concurrent_positions: int = 0


class PortfolioResearchEngine:
    def __init__(self, sleeves: list[ResearchSleeve], limits: PortfolioLimits | None = None,
                 *, swing_price_protection: bool = False, directional_loss_guard: bool = False,
                 swing_failure_exit: bool = False, slope_risk_cap: bool = False,
                 intraday_price_protection: bool = False, swing_short_risk_cap: bool = False,
                 swing_hourly_failure: bool = False, swing_long_signal_hold: bool = False) -> None:
        if type(swing_long_signal_hold) is not bool:
            raise ValueError("swing_long_signal_hold must be boolean")
        self.swing_long_signal_hold = swing_long_signal_hold
        if type(swing_hourly_failure) is not bool or (swing_hourly_failure and not swing_failure_exit):
            raise ValueError("swing_hourly_failure requires boolean and enabled swing_failure_exit")
        self.swing_hourly_failure = swing_hourly_failure
        if type(swing_short_risk_cap) is not bool:
            raise ValueError("swing_short_risk_cap must be boolean")
        self.swing_short_risk_cap = swing_short_risk_cap
        if type(intraday_price_protection) is not bool:
            raise ValueError("intraday_price_protection must be boolean")
        self.intraday_price_protection=intraday_price_protection
        if type(slope_risk_cap) is not bool:
            raise ValueError("slope_risk_cap must be boolean")
        self.slope_risk_cap=slope_risk_cap
        if type(swing_failure_exit) is not bool:
            raise ValueError("swing_failure_exit must be boolean")
        self.swing_failure_exit = swing_failure_exit
        if type(swing_price_protection) is not bool:
            raise ValueError("swing_price_protection must be boolean")
        self.swing_price_protection = swing_price_protection
        if type(directional_loss_guard) is not bool:
            raise ValueError("directional_loss_guard must be boolean")
        self.directional_loss_guard = directional_loss_guard
        if not sleeves or len({s.name for s in sleeves})!=len(sleeves):
            raise ValueError("unique nonempty research sleeves required")
        if any(not s.name for s in sleeves) or len({s.config.initial_cash for s in sleeves})!=1:
            raise ValueError("all sleeves must share one initial account balance")
        self.sleeves=sleeves
        self.limits=limits or PortfolioLimits()
        # Gross exposure <=100% makes >1x unnecessary in this portfolio baseline.
        self.configs={s.name:replace(s.config,max_exposure=min(s.config.max_exposure,self.limits.max_gross_exposure)) for s in sleeves}
        self.engines={name:LongShortResearchEngine(config) for name,config in self.configs.items()}

    def _usage(self,book: dict[str,OpenLot],mark: float):
        lots=[]
        for lot in book.values():
            p,c=lot.position,self.configs[lot.sleeve]
            # Funding remains in the isolated wallet: receiving funding must
            # not make the same collateral available to another strategy.
            lots.append(RiskLot(p.quantity,p.direction,p.stop,max(0,p.margin+p.funding),c.fee_bps,c.slippage_bps,c.funding_reserve))
        return portfolio_usage(lots,mark)

    @staticmethod
    def _equity(cash: float,book: dict[str,OpenLot],mark: float) -> float:
        return cash+sum(l.position.direction*l.position.quantity*(mark-l.position.entry_price) for l in book.values())

    def run(self,candles: list[Candle],*,evaluation_start_ms: int,marks: list[MarkPriceCandle],
            funding: list[FundingRate], signal_observer: Callable[[dict],None] | None = None,
            admission_observer: Callable[[dict],None] | None = None) -> PortfolioResearchResult:
        start=next(iter(self.engines.values())).validate_inputs(candles,
            evaluation_start_ms=evaluation_start_ms,marks=marks,funding=funding)
        initial=self.sleeves[0].config.initial_cash
        cash=initial
        book: dict[str,OpenLot]={}
        trades: list[PortfolioTrade]=[]
        admissions=[]
        admission_by_id: dict[str,dict] = {}
        points=[]
        counts: dict[int,int]={}
        sequence=0
        peak_positions=0
        max_ratio=0.0
        curve=[EquityPoint(evaluation_start_ms-3600000,initial,False)]
        by_hour: dict[int,list[FundingRate]]={}
        for event in funding:
            by_hour.setdefault(event.timestamp_ms//3600000,[]).append(event)

        def close(lot_id: str,candle: Candle,reference: float,reason: str) -> None:
            nonlocal cash
            lot=book.pop(lot_id)
            cash,trade=self.engines[lot.sleeve]._close(cash,lot.position,candle,reference,reason)
            # Preserve initial risk in the trade; active-stop updates have their own audit.
            if lot.initial_stop is not None:
                trade=replace(trade,stop_loss_price=lot.initial_stop)
            trades.append(PortfolioTrade(**asdict(trade),position_id=lot.position_id,sleeve=lot.sleeve))

        def stop_reason(lot: OpenLot) -> str:
            return "profit_protection" if lot.initial_stop is not None and lot.position.stop!=lot.initial_stop else "stop_loss"

        for i in range(start,len(candles)):
            candle,mark=candles[i],marks[i-start]
            history=candles[:i]
            signals={s.name:s.strategy.generate(history) for s in self.sleeves}
            for signal in signals.values():
                action={-1:Action.SELL,0:Action.HOLD,1:Action.BUY}.get(signal.direction)
                if (action is None or signal.action is not action or signal.symbol!=candle.symbol
                        or int(signal.timestamp.timestamp()*1000)!=candles[i-1].timestamp_ms):
                    raise ValueError("portfolio signal must use completed matching hourly history")
            events=by_hour.get(candle.timestamp_ms//3600000,[])
            exited=set()
            for lot_id,lot in list(book.items()):
                p,c=lot.position,self.configs[lot.sleeve]
                for event in events:
                    if event.timestamp_ms<=candle.timestamp_ms:
                        amount=funding_cashflow(p,event);cash+=amount;p.funding+=amount
                balance=p.margin+p.direction*p.quantity*(mark.open-p.entry_price)+p.funding
                if balance<=p.quantity*mark.open*c.assumed_mmr:
                    close(lot_id,candle,mark.open,"liquidation");exited.add(lot.sleeve)
                elif p.direction*(candle.open-p.stop)<=0:
                    close(lot_id,candle,candle.open,stop_reason(lot));exited.add(lot.sleeve)
                else:
                    signal=signals[lot.sleeve]
                    timed=candle.timestamp_ms-p.entry_timestamp_ms>=c.holding_hours*3600000
                    wants_exit=signal.exit_long if p.direction==1 else signal.exit_short
                    # Swing longs ignore strategy exits for the first 72h; stops and failure exits still apply.
                    if (self.swing_long_signal_hold and lot.sleeve=="swing" and p.direction==1
                            and candle.timestamp_ms-p.entry_timestamp_ms<SWING_LONG_SIGNAL_HOLD_HOURS*3600000):
                        wants_exit=False
                    failed=lot.breakout_level is not None and breakout_failed(history,p.direction,lot.breakout_level,hourly=self.swing_hourly_failure)
                    if timed or wants_exit or failed:
                        close(lot_id,candle,candle.open,"time_limit" if timed else "signal" if wants_exit else "breakout_failure")
                        exited.add(lot.sleeve)
            # Stable, declared sleeve order controls competition for shared risk.
            admission_start=len(admissions)
            for sleeve in self.sleeves:
                signal=signals[sleeve.name];c=self.configs[sleeve.name]
                permitted=signal.direction!=0 and (c.mode=="both" or c.mode=="long_only" and signal.direction==1 or c.mode=="short_only" and signal.direction==-1)
                if not permitted or sleeve.name in exited:
                    continue
                day=candle.timestamp_ms//86400000
                if counts.get(day,0)>=self.limits.daily_entries:
                    admissions.append(dict(timestamp_ms=candle.timestamp_ms,sleeve=sleeve.name,status="rejected",reason="daily_entry_limit"))
                    continue
                equity=self._equity(cash,book,mark.open)
                closed=[t.pnl for t in trades if t.sleeve==sleeve.name]
                shared_brake=loss_streak_multiplier(closed) if c.loss_brake else 1
                own_closed=[t.pnl for t in trades if t.sleeve==sleeve.name and t.direction==signal.direction] if self.directional_loss_guard else []
                brake=directional_loss_guard_multiplier(closed,own_closed) if c.loss_brake and self.directional_loss_guard else shared_brake
                multiplier=brake
                slope_cap=directional_slope_cap(history,signal.direction) if self.slope_risk_cap else 1.
                multiplier=min(multiplier,slope_cap)
                sleeve_side_cap = .5 if self.swing_short_risk_cap and sleeve.name == 'swing' and signal.direction == -1 else 1.
                multiplier=min(multiplier,sleeve_side_cap)
                same_direction=sum(l.position.direction==signal.direction for l in book.values())
                if self.limits.same_direction_risk_decay:
                    multiplier/=1+same_direction
                _,proposal=self.engines[sleeve.name]._open(equity,candle,signal,multiplier)
                if proposal is None:
                    admissions.append(dict(timestamp_ms=candle.timestamp_ms,sleeve=sleeve.name,status="rejected",reason="invalidated_entry"))
                    continue
                usage=self._usage(book,mark.open)
                fraction,reason=admission_fraction(equity=equity,cash=cash,usage=usage,
                    notional=proposal.quantity*max(proposal.entry_price,mark.open),margin_and_fee=proposal.margin+proposal.entry_fee,
                    planned_risk=proposal.planned_risk,limits=self.limits)
                if admission_observer is not None:
                    admission_observer(deepcopy(dict(timestamp_ms=candle.timestamp_ms,
                        sleeve=sleeve.name,direction=signal.direction,mark=mark.open,
                        equity=equity,cash=cash,usage=asdict(usage),proposal=asdict(proposal),
                        fraction=fraction,reason=reason,limits=asdict(self.limits),
                        lots=[dict(position_id=lot.position_id,sleeve=lot.sleeve,
                                   position=asdict(lot.position),config=asdict(self.configs[lot.sleeve]))
                              for lot in book.values()])))
                if fraction<=1e-10:
                    admissions.append(dict(timestamp_ms=candle.timestamp_ms,sleeve=sleeve.name,status="rejected",reason=reason))
                    continue
                p=replace(proposal,quantity=proposal.quantity*fraction,margin=proposal.margin*fraction,
                    entry_fee=proposal.entry_fee*fraction,entry_slippage=proposal.entry_slippage*fraction,planned_risk=proposal.planned_risk*fraction)
                sequence+=1
                lot_id=f"{sleeve.name}:{candle.timestamp_ms}:{sequence}"
                cash-=p.entry_fee
                book[lot_id]=OpenLot(lot_id,sleeve.name,p,p.stop)
                if self.swing_failure_exit and sleeve.name=='swing':
                    book[lot_id].breakout_level=breakout_boundary(history,p.direction)
                peak_positions=max(peak_positions,len(book))
                counts[day]=counts.get(day,0)+1
                admissions.append(dict(timestamp_ms=candle.timestamp_ms,sleeve=sleeve.name,status="accepted",reason=reason,
                    position_id=lot_id,direction=p.direction,quantity=p.quantity,scale=fraction,equity_before=equity,
                    cash_before=cash+p.entry_fee,open_positions_after=len(book),
                    gross_before=usage.gross,margin_before=usage.margin,stop_risk_before=usage.open_stop_risk,
                    entry_notional=p.quantity*p.entry_price,mark_at_entry=mark.open,gross_added=p.quantity*mark.open,
                    margin_added=p.margin,entry_fee=p.entry_fee,planned_risk=p.planned_risk))
                admission_by_id[lot_id]=admissions[-1]
                if self.swing_short_risk_cap:
                    admissions[-1]['swing_short_risk_trace'] = dict(
                        cap=sleeve_side_cap, loss_brake=brake, sizing_multiplier=multiplier)
                if self.slope_risk_cap:
                    admissions[-1]['slope_risk_trace']=dict(slope_cap=slope_cap,loss_brake=brake,
                        capped_multiplier=min(brake,slope_cap),sizing_multiplier=multiplier)
                if book[lot_id].breakout_level is not None:
                    admissions[-1]['breakout_level']=book[lot_id].breakout_level
                if self.limits.same_direction_risk_decay:
                    admissions[-1].update(same_direction_before=same_direction,risk_multiplier=multiplier)
                if self.directional_loss_guard:
                    admissions[-1]['loss_guard_trace']=dict(shared_pnls=closed,directional_pnls=own_closed,
                        shared_multiplier=shared_brake,directional_multiplier=loss_streak_multiplier(own_closed) if c.loss_brake else 1,
                        final_brake_multiplier=brake,sizing_multiplier=multiplier)
            if signal_observer is not None:
                current_admissions={a['sleeve']:a for a in admissions[admission_start:]}
                for sleeve in self.sleeves:
                    signal=signals[sleeve.name];c=self.configs[sleeve.name]
                    if signal.direction==0:
                        continue
                    permitted=(c.mode=="both" or c.mode=="long_only" and signal.direction==1
                               or c.mode=="short_only" and signal.direction==-1)
                    if not permitted:
                        outcome=dict(status="skipped",reason="direction_disabled")
                    elif sleeve.name in exited:
                        outcome=dict(status="skipped",reason="open_exit_cooldown")
                    else:
                        if sleeve.name not in current_admissions:
                            raise ValueError("qualified signal missing admission outcome")
                        outcome=deepcopy(current_admissions[sleeve.name])
                    signal_observer(dict(timestamp_ms=candle.timestamp_ms,sleeve=sleeve.name,
                        direction=signal.direction,signal_timestamp_ms=candles[i-1].timestamp_ms,
                        signal_close=candles[i-1].close,stop_loss_price=signal.stop_loss_price,
                        outcome=outcome))
            for lot_id,lot in list(book.items()):
                p,c=lot.position,self.configs[lot.sleeve]
                for event in events:
                    if event.timestamp_ms>candle.timestamp_ms:
                        amount=funding_cashflow(p,event);cash+=amount;p.funding+=amount
                adverse=mark.low if p.direction==1 else mark.high
                balance=p.margin+p.direction*p.quantity*(adverse-p.entry_price)+p.funding
                maintenance=p.quantity*adverse*c.assumed_mmr
                max_ratio=max(max_ratio,maintenance/balance if balance>0 else 1)
                if balance<=maintenance:
                    level=liquidation_price(p,c.assumed_mmr)
                    reference=min(mark.open,level) if p.direction==1 else max(mark.open,level)
                    close(lot_id,candle,reference,"liquidation")
                elif (p.direction==1 and candle.low<=p.stop) or (p.direction==-1 and candle.high>=p.stop):
                    reference=min(candle.open,p.stop) if p.direction==1 else max(candle.open,p.stop)
                    close(lot_id,candle,reference,stop_reason(lot))
            # All current-bar extremes/closures are processed before this close-only update.
            if (self.swing_price_protection or self.intraday_price_protection) and i<len(candles)-1:
                for lot_id,lot in book.items():
                    p=lot.position
                    protected_sleeve=(lot.sleeve=='swing' and self.swing_price_protection
                                      or lot.sleeve=='intraday' and self.intraday_price_protection)
                    if not protected_sleeve or lot.initial_stop is None:
                        continue
                    initial_distance=abs(p.entry_price-lot.initial_stop)
                    if (initial_distance>0 and p.direction*(candle.close-p.entry_price)>=initial_distance
                            and p.direction*(p.entry_price-p.stop)>0):
                        old_stop=p.stop
                        p.stop=p.entry_price
                        admission_by_id[lot_id].setdefault("stop_updates",[]).append(dict(
                            decision_timestamp_ms=candle.timestamp_ms,active_from_ms=candle.timestamp_ms+3600000,
                            trigger_close=candle.close,initial_stop=lot.initial_stop,
                            from_stop=old_stop,to_stop=p.stop,activation_r=1.0))
            if i==len(candles)-1:
                for lot_id in list(book):
                    close(lot_id,candle,candle.close,"end_of_data")
            equity=self._equity(cash,book,mark.close)
            if equity<=0 or not isfinite(equity):
                raise ValueError("portfolio account insolvent; scenario failed")
            usage=self._usage(book,mark.close)
            exceeded=(usage.gross>equity*self.limits.max_gross_exposure+1e-7 or
                      usage.open_stop_risk>equity*self.limits.max_open_stop_risk+1e-7 or
                      usage.margin>equity*self.limits.max_margin_fraction+1e-7)
            points.append(PortfolioPoint(candle.timestamp_ms,equity,cash,len(book),usage.gross,usage.net,
                usage.margin,usage.open_stop_risk,exceeded))
            curve.append(EquityPoint(candle.timestamp_ms,equity,bool(book)))
        if abs(cash-initial-sum(t.pnl for t in trades))>1e-6:
            raise ValueError("shared account cash/PnL does not reconcile")
        metrics=calculate_metrics(curve,trades,initial,"1h",max_ratio)
        return PortfolioResearchResult("perpetual_multi_position_portfolio",candles[0].symbol,"1h",
            initial,cash,metrics,trades,curve,points,admissions,peak_positions)
