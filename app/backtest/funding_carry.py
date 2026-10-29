"""Delta-neutral BTC funding carry research: long spot plus equal short USDT perpetual.

Rules are frozen in docs/research/2026-10-29-funding-carry-design.md. Research
only: wallet transfers are assumed free and instant, historical margin brackets
are unverified, and exchange counterparty risk is not modelled.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from math import isfinite

from app.backtest.metrics import calculate_metrics
from app.backtest.models import EquityPoint
from app.data.models import Candle, FundingRate, MarkPriceCandle

HOUR_MS = 3600000


@dataclass(frozen=True)
class CarryConfig:
    perp_fee_bps: float
    perp_slippage_bps: float
    spot_fee_bps: float
    spot_slippage_bps: float
    initial_cash: float = 10000
    target_fraction: float = 2 / 3
    assumed_mmr: float = .02
    liquidation_fee_bps: float = 50
    emergency_margin_ratio: float = .25
    # 0 disables; otherwise rebalance when spot value exceeds target by this fraction (experiment 3).
    drift_band: float = 0
    # 0 disables; otherwise hold only while the last N published funding rates sum above zero.
    pause_funding_events: int = 0

    def __post_init__(self) -> None:
        values = (self.perp_fee_bps, self.perp_slippage_bps, self.spot_fee_bps, self.spot_slippage_bps)
        if not all(isfinite(v) and 0 <= v < 1000 for v in values):
            raise ValueError("invalid carry costs")
        if not (isfinite(self.drift_band) and 0 <= self.drift_band < 1):
            raise ValueError("invalid drift band")
        if type(self.pause_funding_events) is not int or self.pause_funding_events < 0:
            raise ValueError("invalid funding pause window")
        if not (0 < self.target_fraction < 1 and self.initial_cash > 0 and 0 < self.emergency_margin_ratio < 1):
            raise ValueError("invalid carry sizing")


@dataclass
class CarryBook:
    config: CarryConfig
    spot_qty: float = 0
    spot_cash: float = 0
    short_qty: float = 0
    short_entry: float = 0
    perp_wallet: float = 0
    fees: float = 0
    slippage: float = 0
    funding: float = 0
    liquidation_fee: float = 0
    rebalances: list[dict] = field(default_factory=list)

    def equity(self, spot: float, perp: float) -> float:
        return self.spot_cash + self.spot_qty * spot + self.perp_wallet + self.short_qty * (self.short_entry - perp)

    def perp_equity(self, mark: float) -> float:
        return self.perp_wallet + self.short_qty * (self.short_entry - mark)

    def _trade_spot(self, quantity: float, price: float) -> None:
        c = self.config
        side = 1 if quantity > 0 else -1
        fill = price * (1 + side * c.spot_slippage_bps / 10000)
        fee = abs(quantity) * fill * c.spot_fee_bps / 10000
        self.spot_cash -= quantity * fill + fee
        self.spot_qty += quantity
        self.fees += fee
        self.slippage += abs(quantity) * price * c.spot_slippage_bps / 10000

    def _trade_short(self, change: float, price: float) -> None:
        """change > 0 adds short quantity (sell); change < 0 buys back."""
        c = self.config
        fill = price * (1 - (1 if change > 0 else -1) * c.perp_slippage_bps / 10000)
        fee = abs(change) * fill * c.perp_fee_bps / 10000
        if change > 0:
            self.short_entry = (self.short_qty * self.short_entry + change * fill) / (self.short_qty + change)
        else:
            self.perp_wallet += -change * (self.short_entry - fill)
        self.short_qty += change
        self.perp_wallet -= fee
        self.fees += fee
        self.slippage += abs(change) * price * c.perp_slippage_bps / 10000

    def rebalance(self, timestamp_ms: int, spot_open: float, perp_open: float, reason: str) -> None:
        before = self.equity(spot_open, perp_open)
        target = self.config.target_fraction * before / spot_open
        if target != self.spot_qty:
            self._trade_spot(target - self.spot_qty, spot_open)
        if target != self.short_qty:
            self._trade_short(target - self.short_qty, perp_open)
        after = self.equity(spot_open, perp_open)
        # Pool USDT so the perp wallet holds equity minus spot value; spot cash becomes zero.
        usdt = self.spot_cash + self.perp_wallet
        self.perp_wallet = after - self.spot_qty * spot_open - self.short_qty * (self.short_entry - perp_open)
        self.spot_cash = usdt - self.perp_wallet
        self.rebalances.append(dict(timestamp_ms=timestamp_ms, reason=reason, equity_before=before,
                                    equity_after=after, quantity=target))

    def flatten(self, timestamp_ms: int, spot_open: float, perp_open: float, reason: str) -> None:
        """Close both legs and hold USDT only (funding pause)."""
        before = self.equity(spot_open, perp_open)
        if self.short_qty:
            self._trade_short(-self.short_qty, perp_open)
        if self.spot_qty:
            self._trade_spot(-self.spot_qty, spot_open)
        self.spot_cash += self.perp_wallet
        self.perp_wallet = 0
        self.rebalances.append(dict(timestamp_ms=timestamp_ms, reason=reason, equity_before=before,
                                    equity_after=self.spot_cash, quantity=0.0))

    def apply_funding(self, event: FundingRate) -> None:
        amount = self.short_qty * event.mark_price * event.rate
        self.perp_wallet += amount
        self.funding += amount

    def liquidated_by(self, mark_high: float) -> float | None:
        """Liquidation reference level if the short wallet breaches maintenance at mark_high."""
        q = self.short_qty
        if q <= 0 or self.perp_equity(mark_high) > q * mark_high * self.config.assumed_mmr:
            return None
        return (self.perp_wallet + q * self.short_entry) / (q * (1 + self.config.assumed_mmr))

    def liquidate(self, reference: float) -> None:
        q = self.short_qty
        fee = q * reference * self.config.liquidation_fee_bps / 10000
        self.perp_wallet += q * (self.short_entry - reference) - fee
        self.liquidation_fee += fee
        self.short_qty = 0


def _month_start(timestamp_ms: int) -> bool:
    d = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
    return d.day == 1 and d.hour == 0


def run_funding_carry(perp: list[Candle], marks: list[MarkPriceCandle], funding: list[FundingRate],
                      spot: dict[int, Candle], config: CarryConfig,
                      known_spot_outages: frozenset[int] = frozenset(), record_hourly: bool = False,
                      funding_history: list[FundingRate] = ()) -> dict:
    """funding_history: events before the period, used only for the pause signal."""
    if not perp or [m.timestamp_ms for m in marks] != [c.timestamp_ms for c in perp]:
        raise ValueError("aligned hourly perpetual candles and marks required")
    if any(b.timestamp_ms - a.timestamp_ms != HOUR_MS for a, b in zip(perp, perp[1:])):
        raise ValueError("gapped perpetual tape")
    missing = {c.timestamp_ms for c in perp} - set(spot)
    if missing - known_spot_outages:
        raise ValueError("spot candles missing outside registered outages")
    if perp[0].timestamp_ms in missing or perp[-1].timestamp_ms in missing:
        raise ValueError("spot required at entry and exit hours")
    by_hour: dict[int, list[FundingRate]] = {}
    for event in funding:
        by_hour.setdefault(event.timestamp_ms // HOUR_MS * HOUR_MS, []).append(event)
    book = CarryBook(config, spot_cash=config.initial_cash)
    curve = [EquityPoint(perp[0].timestamp_ms - HOUR_MS, config.initial_cash, False)]
    window = config.pause_funding_events
    pending: str | None = None if window else "entry"
    seen = [e.rate for e in sorted(funding_history, key=lambda e: e.timestamp_ms) if e.timestamp_ms < perp[0].timestamp_ms]
    liquidated_at = None
    max_leverage = max_margin_ratio = 0.0
    last_spot_close = None
    basis = []
    hourly = []
    for i, candle in enumerate(perp):
        t, mark = candle.timestamp_ms, marks[i]
        spot_bar = spot.get(t)
        events = by_hour.get(t, [])
        for event in events:
            if event.timestamp_ms <= t:
                book.apply_funding(event)
                seen.append(event.rate)
        if window and liquidated_at is None and spot_bar is not None and i < len(perp) - 1:
            hold = len(seen) >= window and sum(seen[-window:]) > 0
            if book.short_qty and not hold:
                book.flatten(t, spot_bar.open, candle.open, "pause")
                pending = None
            elif not book.short_qty and hold and pending is None:
                pending = "resume" if book.rebalances else "entry"
        if liquidated_at is None and _month_start(t) and i > 0 and (not window or book.short_qty):
            pending = pending or "monthly"
        if pending and spot_bar is not None and liquidated_at is None:
            book.rebalance(t, spot_bar.open, candle.open, pending)
            pending = None
        for event in events:
            if event.timestamp_ms > t:
                book.apply_funding(event)
                seen.append(event.rate)
        level = book.liquidated_by(mark.high)
        if level is not None:
            book.liquidate(max(mark.open, level))
            liquidated_at = t
        spot_close = spot_bar.close if spot_bar is not None else last_spot_close
        last_spot_close = spot_close
        if i == len(perp) - 1:
            if book.short_qty:
                book._trade_short(-book.short_qty, candle.close)
            book._trade_spot(-book.spot_qty, spot_close)
        equity = book.equity(spot_close, mark.close)
        if equity <= 0 or not isfinite(equity):
            raise ValueError("carry account insolvent")
        curve.append(EquityPoint(t, equity, book.short_qty > 0))
        if record_hourly:
            hourly.append(dict(timestamp_ms=t, spot_value=book.spot_qty * spot_close,
                               short_notional=book.short_qty * mark.close, perp_equity=book.perp_equity(mark.close)))
        if book.short_qty:
            perp_equity = book.perp_equity(mark.close)
            max_leverage = max(max_leverage, book.short_qty * mark.close / perp_equity)
            max_margin_ratio = max(max_margin_ratio, book.short_qty * mark.high * config.assumed_mmr
                                   / max(book.perp_equity(mark.high), 1e-9))
            basis.append(candle.close / spot_close - 1)
            if perp_equity / (book.short_qty * mark.close) < config.emergency_margin_ratio and pending is None:
                pending = "emergency"
            if (config.drift_band and pending is None and i < len(perp) - 1
                    and book.spot_qty * spot_close > config.target_fraction * equity * (1 + config.drift_band)):
                pending = "drift"
    final = curve[-1].equity
    if abs(book.spot_cash + book.perp_wallet - final) > 1e-6 or book.spot_qty > 1e-12 or book.short_qty:
        raise ValueError("carry account does not reconcile after exit")
    metrics = calculate_metrics(curve, [], config.initial_cash, "1h", max_margin_ratio)
    return dict(metrics=asdict(metrics), final_equity=final,
                funding_income=book.funding, fees=book.fees, slippage=book.slippage,
                liquidation_fee=book.liquidation_fee, liquidated_at_ms=liquidated_at,
                rebalances=book.rebalances, emergency_rebalances=sum(r["reason"] == "emergency" for r in book.rebalances),
                maximum_perp_leverage=max_leverage, maximum_margin_ratio=max_margin_ratio,
                basis_min=min(basis) if basis else None, basis_max=max(basis) if basis else None,
                pauses=sum(r["reason"] == "pause" for r in book.rebalances),
                invested_hours=sum(p.invested for p in curve),
                spot_outage_hours=sorted(missing), equity_curve=[(p.timestamp_ms, p.equity) for p in curve],
                **(dict(hourly=hourly) if record_hourly else {}))
