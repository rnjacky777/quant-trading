"""Paper-only BTC perpetual portfolio book for the frozen forward observation.

Decision semantics mirror PortfolioResearchEngine with the frozen flags
(directional_loss_guard, swing_failure_exit). The caller supplies prices:
the replay driver passes next-open and bar extremes (parity check), the live
paper runner passes observed quotes. No order or exchange method exists here.
"""
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from math import isfinite

from app.backtest.long_short_research import (LongShortResearchEngine, funding_cashflow,
    liquidation_price)
from app.backtest.portfolio_research import OpenLot, PortfolioPoint, PortfolioTrade, ResearchSleeve
from app.data.models import Candle, FundingRate
from app.portfolio.research_risk import PortfolioLimits, PortfolioUsage, RiskLot, admission_fraction, portfolio_usage
from app.risk.regime import directional_loss_guard_multiplier, loss_streak_multiplier
from app.strategies.base import Action
from app.strategies.directional_intraday import DirectionalSignal
from app.strategies.swing_failure import breakout_boundary, breakout_failed

HOUR_MS = 3600000


@dataclass(frozen=True)
class FillPrices:
    """Reference prices before adverse slippage: buys use ask, sells use bid."""
    buy: float
    sell: float

    def __post_init__(self) -> None:
        if not (isfinite(self.buy) and isfinite(self.sell) and 0 < self.sell <= self.buy):
            raise ValueError("fill prices need finite positive bid <= ask")

    def opening(self, direction: int) -> float:
        return self.buy if direction == 1 else self.sell

    def closing(self, direction: int) -> float:
        return self.sell if direction == 1 else self.buy


@dataclass(frozen=True)
class FillRecord:
    position_id: str
    side: str
    reason: str
    decision_hour_ms: int
    fill_ms: int
    reference_price: float


def sleeve_signals(sleeves: list[ResearchSleeve], history: list[Candle]) -> dict[str, DirectionalSignal]:
    """Signals from completed hourly history only, validated like the research engine."""
    signals = {s.name: s.strategy.generate(history) for s in sleeves}
    for signal in signals.values():
        action = {-1: Action.SELL, 0: Action.HOLD, 1: Action.BUY}.get(signal.direction)
        if (action is None or signal.action is not action or signal.symbol != history[-1].symbol
                or int(signal.timestamp.timestamp() * 1000) != history[-1].timestamp_ms):
            raise ValueError("portfolio signal must use completed matching hourly history")
    return signals


@dataclass
class PaperPortfolioBook:
    sleeves: list[ResearchSleeve]
    limits: PortfolioLimits = field(default_factory=PortfolioLimits)

    def __post_init__(self) -> None:
        if not self.sleeves or len({s.name for s in self.sleeves}) != len(self.sleeves):
            raise ValueError("unique nonempty research sleeves required")
        if len({s.config.initial_cash for s in self.sleeves}) != 1:
            raise ValueError("all sleeves must share one initial account balance")
        if self.limits.same_direction_risk_decay:
            raise ValueError("frozen paper observation has same-direction risk decay disabled")
        self.configs = {s.name: replace(s.config, max_exposure=min(s.config.max_exposure,
                        self.limits.max_gross_exposure)) for s in self.sleeves}
        self.engines = {name: LongShortResearchEngine(c) for name, c in self.configs.items()}
        self.initial_cash = self.sleeves[0].config.initial_cash
        self.cash = self.initial_cash
        self.book: dict[str, OpenLot] = {}
        self.trades: list[PortfolioTrade] = []
        self.admissions: list[dict] = []
        self.fills: list[FillRecord] = []
        self.points: list[PortfolioPoint] = []
        self.counts: dict[int, int] = {}
        self.applied_funding: set[int] = set()
        self.sequence = 0
        self.peak_positions = 0
        self.max_ratio = 0.0

    def usage(self, mark: float) -> PortfolioUsage:
        lots = []
        for lot in self.book.values():
            p, c = lot.position, self.configs[lot.sleeve]
            lots.append(RiskLot(p.quantity, p.direction, p.stop, max(0, p.margin + p.funding),
                                c.fee_bps, c.slippage_bps, c.funding_reserve))
        return portfolio_usage(lots, mark)

    def equity(self, mark: float) -> float:
        return self.cash + sum(l.position.direction * l.position.quantity * (mark - l.position.entry_price)
                               for l in self.book.values())

    @staticmethod
    def _at(identity: Candle, hour_ms: int, price: float) -> Candle:
        # Research helpers read only timestamp and open; the hour keeps time-limit semantics.
        return Candle(identity.exchange, identity.symbol, "1h", hour_ms, price, price, price, price, 0)

    def _register_funding(self, events: list[FundingRate]) -> None:
        if any(e.timestamp_ms in self.applied_funding for e in events) or len({e.timestamp_ms for e in events}) != len(events):
            raise ValueError("duplicate funding event")
        self.applied_funding.update(e.timestamp_ms for e in events)

    def settle_funding(self, events: list[FundingRate]) -> None:
        """Funding without a decision or risk check, e.g. a boundary whose bar or quote was missing."""
        self._register_funding(events)
        for lot in self.book.values():
            self._fund(lot, events)

    def _fund(self, lot: OpenLot, events: list[FundingRate]) -> None:
        # Applied per lot before that lot's checks, matching research float order.
        for event in events:
            amount = funding_cashflow(lot.position, event)
            self.cash += amount
            lot.position.funding += amount

    def _close(self, lot_id: str, identity: Candle, hour_ms: int, reference: float,
               reason: str, fill_ms: int) -> None:
        lot = self.book.pop(lot_id)
        self.cash, trade = self.engines[lot.sleeve]._close(self.cash, lot.position,
                                                           self._at(identity, hour_ms, reference), reference, reason)
        if lot.initial_stop is not None:
            trade = replace(trade, stop_loss_price=lot.initial_stop)
        self.trades.append(PortfolioTrade(**asdict(trade), position_id=lot.position_id, sleeve=lot.sleeve))
        self.fills.append(FillRecord(lot_id, "sell" if lot.position.direction == 1 else "buy",
                                     reason, hour_ms, fill_ms, reference))

    @staticmethod
    def _stop_reason(lot: OpenLot) -> str:
        return "profit_protection" if lot.initial_stop is not None and lot.position.stop != lot.initial_stop else "stop_loss"

    def open_phase(self, *, hour_ms: int, history: list[Candle], signals: dict[str, DirectionalSignal],
                   trigger: float, prices: FillPrices, mark: float, fill_ms: int,
                   funding: list[FundingRate] = (), allow_entries: bool = True) -> set[str]:
        """Funding due by the boundary, exits, then shared-budget admissions; returns exited sleeves."""
        identity = history[-1]
        exited: set[str] = set()
        self._register_funding(list(funding))
        for lot_id, lot in list(self.book.items()):
            p, c = lot.position, self.configs[lot.sleeve]
            self._fund(lot, list(funding))
            balance = p.margin + p.direction * p.quantity * (mark - p.entry_price) + p.funding
            if balance <= p.quantity * mark * c.assumed_mmr:
                self._close(lot_id, identity, hour_ms, mark, "liquidation", fill_ms); exited.add(lot.sleeve)
            elif p.direction * (trigger - p.stop) <= 0:
                self._close(lot_id, identity, hour_ms, prices.closing(p.direction), self._stop_reason(lot), fill_ms)
                exited.add(lot.sleeve)
            else:
                signal = signals[lot.sleeve]
                timed = hour_ms - p.entry_timestamp_ms >= c.holding_hours * HOUR_MS
                wants_exit = signal.exit_long if p.direction == 1 else signal.exit_short
                failed = lot.breakout_level is not None and breakout_failed(history, p.direction, lot.breakout_level)
                if timed or wants_exit or failed:
                    self._close(lot_id, identity, hour_ms, prices.closing(p.direction),
                                "time_limit" if timed else "signal" if wants_exit else "breakout_failure", fill_ms)
                    exited.add(lot.sleeve)
        for sleeve in self.sleeves:
            signal, c = signals[sleeve.name], self.configs[sleeve.name]
            permitted = signal.direction != 0 and (c.mode == "both" or c.mode == "long_only" and signal.direction == 1
                                                   or c.mode == "short_only" and signal.direction == -1)
            if not permitted or sleeve.name in exited:
                continue
            if not allow_entries:
                self.admissions.append(dict(timestamp_ms=hour_ms, sleeve=sleeve.name, status="rejected",
                                            reason="data_quality_block"))
                continue
            day = hour_ms // 86400000
            if self.counts.get(day, 0) >= self.limits.daily_entries:
                self.admissions.append(dict(timestamp_ms=hour_ms, sleeve=sleeve.name, status="rejected",
                                            reason="daily_entry_limit"))
                continue
            equity = self.equity(mark)
            closed = [t.pnl for t in self.trades if t.sleeve == sleeve.name]
            shared_brake = loss_streak_multiplier(closed) if c.loss_brake else 1
            own_closed = [t.pnl for t in self.trades if t.sleeve == sleeve.name and t.direction == signal.direction]
            brake = directional_loss_guard_multiplier(closed, own_closed) if c.loss_brake else shared_brake
            reference = prices.opening(signal.direction)
            _, proposal = self.engines[sleeve.name]._open(equity, self._at(identity, hour_ms, reference), signal, brake)
            if proposal is None:
                self.admissions.append(dict(timestamp_ms=hour_ms, sleeve=sleeve.name, status="rejected",
                                            reason="invalidated_entry"))
                continue
            usage = self.usage(mark)
            fraction, reason = admission_fraction(equity=equity, cash=self.cash, usage=usage,
                notional=proposal.quantity * max(proposal.entry_price, mark),
                margin_and_fee=proposal.margin + proposal.entry_fee, planned_risk=proposal.planned_risk,
                limits=self.limits)
            if fraction <= 1e-10:
                self.admissions.append(dict(timestamp_ms=hour_ms, sleeve=sleeve.name, status="rejected", reason=reason))
                continue
            p = replace(proposal, quantity=proposal.quantity * fraction, margin=proposal.margin * fraction,
                        entry_fee=proposal.entry_fee * fraction, entry_slippage=proposal.entry_slippage * fraction,
                        planned_risk=proposal.planned_risk * fraction)
            self.sequence += 1
            lot_id = f"{sleeve.name}:{hour_ms}:{self.sequence}"
            self.cash -= p.entry_fee
            self.book[lot_id] = OpenLot(lot_id, sleeve.name, p, p.stop)
            if sleeve.name == "swing":
                self.book[lot_id].breakout_level = breakout_boundary(history, p.direction)
            self.peak_positions = max(self.peak_positions, len(self.book))
            self.counts[day] = self.counts.get(day, 0) + 1
            self.fills.append(FillRecord(lot_id, "buy" if p.direction == 1 else "sell", "entry",
                                         hour_ms, fill_ms, reference))
            self.admissions.append(dict(timestamp_ms=hour_ms, sleeve=sleeve.name, status="accepted", reason=reason,
                position_id=lot_id, direction=p.direction, quantity=p.quantity, scale=fraction, equity_before=equity,
                cash_before=self.cash + p.entry_fee, open_positions_after=len(self.book),
                gross_before=usage.gross, margin_before=usage.margin, stop_risk_before=usage.open_stop_risk,
                entry_notional=p.quantity * p.entry_price, mark_at_entry=mark, gross_added=p.quantity * mark,
                margin_added=p.margin, entry_fee=p.entry_fee, planned_risk=p.planned_risk))
            if self.book[lot_id].breakout_level is not None:
                self.admissions[-1]["breakout_level"] = self.book[lot_id].breakout_level
            self.admissions[-1]["loss_guard_trace"] = dict(shared_pnls=closed, directional_pnls=own_closed,
                shared_multiplier=shared_brake,
                directional_multiplier=loss_streak_multiplier(own_closed) if c.loss_brake else 1,
                final_brake_multiplier=brake, sizing_multiplier=brake)
        return exited

    def check_risk(self, *, hour_ms: int, identity: Candle, trade_low: float, trade_high: float,
                   mark_low: float, mark_high: float, liquidation_reference: Callable[[OpenLot, float], float],
                   stop_reference: Callable[[OpenLot], float], fill_ms: int,
                   funding: list[FundingRate] = ()) -> None:
        """Funding published inside the hour, then liquidation (mark) and stop (trade price) checks."""
        self._register_funding(list(funding))
        for lot_id, lot in list(self.book.items()):
            p, c = lot.position, self.configs[lot.sleeve]
            self._fund(lot, list(funding))
            adverse = mark_low if p.direction == 1 else mark_high
            balance = p.margin + p.direction * p.quantity * (adverse - p.entry_price) + p.funding
            maintenance = p.quantity * adverse * c.assumed_mmr
            self.max_ratio = max(self.max_ratio, maintenance / balance if balance > 0 else 1)
            if balance <= maintenance:
                level = liquidation_price(p, c.assumed_mmr)
                self._close(lot_id, identity, hour_ms, liquidation_reference(lot, level), "liquidation", fill_ms)
            elif (p.direction == 1 and trade_low <= p.stop) or (p.direction == -1 and trade_high >= p.stop):
                self._close(lot_id, identity, hour_ms, stop_reference(lot), self._stop_reason(lot), fill_ms)

    def risk_triggered(self, trade_price: float, mark: float) -> bool:
        """Whether a live observation would close any lot; lets the runner log only acting ticks."""
        for lot in self.book.values():
            p, c = lot.position, self.configs[lot.sleeve]
            balance = p.margin + p.direction * p.quantity * (mark - p.entry_price) + p.funding
            if balance <= p.quantity * mark * c.assumed_mmr or p.direction * (trade_price - p.stop) <= 0:
                return True
        return False

    def observe_margin(self, mark_low: float, mark_high: float) -> None:
        for lot in self.book.values():
            p, c = lot.position, self.configs[lot.sleeve]
            adverse = mark_low if p.direction == 1 else mark_high
            balance = p.margin + p.direction * p.quantity * (adverse - p.entry_price) + p.funding
            self.max_ratio = max(self.max_ratio, p.quantity * adverse * c.assumed_mmr / balance if balance > 0 else 1)

    def close_all(self, *, hour_ms: int, identity: Candle, prices: FillPrices, reason: str, fill_ms: int) -> None:
        for lot_id in list(self.book):
            self._close(lot_id, identity, hour_ms, prices.closing(self.book[lot_id].position.direction), reason, fill_ms)

    def mark_point(self, hour_ms: int, mark: float) -> PortfolioPoint:
        equity = self.equity(mark)
        if equity <= 0 or not isfinite(equity):
            raise ValueError("paper account insolvent; scenario failed")
        usage = self.usage(mark)
        exceeded = (usage.gross > equity * self.limits.max_gross_exposure + 1e-7 or
                    usage.open_stop_risk > equity * self.limits.max_open_stop_risk + 1e-7 or
                    usage.margin > equity * self.limits.max_margin_fraction + 1e-7)
        point = PortfolioPoint(hour_ms, equity, self.cash, len(self.book), usage.gross, usage.net,
                               usage.margin, usage.open_stop_risk, exceeded)
        self.points.append(point)
        return point
