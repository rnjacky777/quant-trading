"""Paper funding-carry book: long spot plus equal short perpetual, priced from observed quotes.

Rules follow the funding-carry research ledger (monthly, emergency and optional
drift rebalances; see docs/research/2026-10-29-funding-carry-design.md and the
coupled design). Fills: buys at ask, sells at bid, then adverse slippage bps.
Wallet transfers are assumed free and instant. No order or exchange method.
"""
from datetime import datetime, timezone

from app.backtest.funding_carry import CarryBook, CarryConfig
from app.data.live_perpetual import Quote
from app.data.models import FundingRate


def month_start(hour_ms: int) -> bool:
    d = datetime.fromtimestamp(hour_ms / 1000, timezone.utc)
    return d.day == 1 and d.hour == 0


class PaperCarryBook:
    def __init__(self, config: CarryConfig) -> None:
        self.config = config
        self.book = CarryBook(config, spot_cash=config.initial_cash)
        self.initial_cash = config.initial_cash
        self.pending: str | None = "entry"
        self.liquidated_at: int | None = None
        self.applied_funding: set[int] = set()
        self.points: list[tuple[int, float]] = []
        self.last_spot: float | None = None
        self.closed = False

    def settle_funding(self, events: list[FundingRate]) -> None:
        stamps = [e.timestamp_ms for e in events]
        if len(set(stamps)) != len(stamps) or any(t in self.applied_funding for t in stamps):
            raise ValueError("duplicate funding event")
        for event in events:
            self.applied_funding.add(event.timestamp_ms)
            self.book.apply_funding(event)

    def equity(self, spot: float, mark: float) -> float:
        return self.book.equity(spot, mark)

    def on_decision(self, hour_ms: int, spot: Quote | None, perp: Quote | None, *, first_hour: bool) -> str | None:
        """Schedule month-start rebalances and execute any pending one; returns the executed reason."""
        if self.closed or self.liquidated_at is not None:
            return None
        if month_start(hour_ms) and not first_hour:
            self.pending = self.pending or "monthly"
        if self.pending is None or spot is None or perp is None:
            return None
        reason, self.pending = self.pending, None
        self._rebalance(hour_ms, spot, perp, reason)
        return reason

    def _rebalance(self, hour_ms: int, spot: Quote, perp: Quote, reason: str) -> None:
        b = self.book
        spot_mid, perp_mid = (spot.bid + spot.ask) / 2, (perp.bid + perp.ask) / 2
        before = b.equity(spot_mid, perp_mid)
        target = self.config.target_fraction * before / spot_mid
        if target != b.spot_qty:
            b._trade_spot(target - b.spot_qty, spot.ask if target > b.spot_qty else spot.bid)
        if target != b.short_qty:
            b._trade_short(target - b.short_qty, perp.bid if target > b.short_qty else perp.ask)
        after = b.equity(spot_mid, perp_mid)
        usdt = b.spot_cash + b.perp_wallet
        b.perp_wallet = after - b.spot_qty * spot_mid - b.short_qty * (b.short_entry - perp_mid)
        b.spot_cash = usdt - b.perp_wallet
        b.rebalances.append(dict(timestamp_ms=hour_ms, reason=reason, equity_before=before, equity_after=after,
                                 quantity=target, spot_fill_ms=spot.received_ms, perp_fill_ms=perp.received_ms))

    def risk_triggered(self, mark: float) -> bool:
        return not self.closed and self.book.liquidated_by(mark) is not None

    def on_tick(self, hour_ms: int, mark: float) -> None:
        if self.closed:
            return
        level = self.book.liquidated_by(mark)
        if level is not None:
            self.book.liquidate(max(mark, level))
            self.liquidated_at = hour_ms

    def on_close(self, hour_ms: int, spot_last: float | None, mark_close: float) -> None:
        spot = spot_last if spot_last is not None else self.last_spot
        if spot is None:
            return
        self.last_spot = spot
        b = self.book
        equity = b.equity(spot, mark_close)
        self.points.append((hour_ms, equity))
        if self.closed or not b.short_qty or self.pending is not None:
            return
        if b.perp_equity(mark_close) / (b.short_qty * mark_close) < self.config.emergency_margin_ratio:
            self.pending = "emergency"
        elif (self.config.drift_band and
              b.spot_qty * spot > self.config.target_fraction * equity * (1 + self.config.drift_band)):
            self.pending = "drift"

    def close_all(self, hour_ms: int, spot: Quote, perp: Quote) -> None:
        if self.closed:
            return
        b = self.book
        if b.short_qty:
            b._trade_short(-b.short_qty, perp.ask)
        if b.spot_qty:
            b._trade_spot(-b.spot_qty, spot.bid)
        self.closed = True
        self.points.append((hour_ms, b.spot_cash + b.perp_wallet))

    def hedge_issues(self) -> list[str]:
        b = self.book
        issues = []
        if self.liquidated_at is None and not self.closed and abs(b.spot_qty - b.short_qty) > 1e-9:
            issues.append("hedge_quantity_mismatch")
        if b.spot_qty < -1e-12 or b.short_qty < -1e-12:
            issues.append("negative_quantity")
        return issues
