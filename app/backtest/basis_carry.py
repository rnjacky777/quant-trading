"""BTC quarterly basis carry research: long spot plus equal short USDT-M quarterly delivery contract.

Rules are frozen in docs/research/2026-10-30-basis-carry-design.md. Accounting reuses
`CarryBook` (no funding on delivery contracts). Research only; not a paper source.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite

from app.backtest.funding_carry import CarryBook, CarryConfig, HOUR_MS
from app.backtest.metrics import calculate_metrics
from app.backtest.models import EquityPoint
from app.data.models import Candle, MarkPriceCandle

ROLL_BEFORE_MS = 24 * HOUR_MS


@dataclass(frozen=True)
class Contract:
    code: str
    delivery_ms: int
    candles: dict[int, Candle]
    marks: dict[int, MarkPriceCandle]


def annualized_basis(future_open: float, spot_open: float, timestamp_ms: int, delivery_ms: int) -> float:
    return (future_open / spot_open - 1) * 8760 / ((delivery_ms - timestamp_ms) / HOUR_MS)


def front(contracts: list[Contract], timestamp_ms: int) -> Contract:
    """Nearest contract whose roll time has not arrived; contracts sorted by delivery."""
    return next(c for c in contracts if timestamp_ms < c.delivery_ms - ROLL_BEFORE_MS)


def run_basis_carry(spot: dict[int, Candle], contracts: list[Contract], config: CarryConfig, threshold: float,
                    start_ms: int, end_ms: int, known_spot_outages: frozenset[int] = frozenset()) -> dict:
    contracts = sorted(contracts, key=lambda c: c.delivery_ms)
    hours = range(start_ms, end_ms, HOUR_MS)
    missing = {t for t in hours if t not in spot}
    if missing - known_spot_outages or start_ms in missing or hours[-1] in missing:
        raise ValueError("spot candles missing outside registered outages")
    book = CarryBook(config, spot_cash=config.initial_cash)
    curve = [EquityPoint(start_ms - HOUR_MS, config.initial_cash, False)]
    held: Contract | None = None
    pending: str | None = None
    liquidated_at = None
    last_spot_close = None
    max_leverage = max_margin_ratio = 0.0
    entries = []
    for t in hours:
        spot_bar = spot.get(t)
        current = front(contracts, t)
        if held is not None and held is not current and liquidated_at is None:
            if spot_bar is None:
                raise ValueError("spot required at roll hour")
            book._trade_short(-book.short_qty, held.candles[t].open)
            held = None
            basis = annualized_basis(current.candles[t].open, spot_bar.open, t, current.delivery_ms)
            if basis > threshold:
                held = current
                book.rebalance(t, spot_bar.open, current.candles[t].open, "roll")
                entries.append(dict(timestamp_ms=t, contract=current.code, annualized_basis=basis, reason="roll"))
            else:
                book._trade_spot(-book.spot_qty, spot_bar.open)
                book.rebalances.append(dict(timestamp_ms=t, reason="roll_to_cash", annualized_basis=basis))
            pending = None
        if held is None and liquidated_at is None and spot_bar is not None and t < hours[-1] and (
                t == start_ms or t % (24 * HOUR_MS) == 0) and not book.spot_qty:
            basis = annualized_basis(current.candles[t].open, spot_bar.open, t, current.delivery_ms)
            if basis > threshold:
                held = current
                book.rebalance(t, spot_bar.open, current.candles[t].open, "entry")
                entries.append(dict(timestamp_ms=t, contract=current.code, annualized_basis=basis, reason="entry"))
        d = datetime.fromtimestamp(t / 1000, timezone.utc)
        if held is not None and liquidated_at is None and d.day == 1 and d.hour == 0 and t != start_ms:
            pending = pending or "monthly"
        if pending and held is not None and spot_bar is not None and liquidated_at is None:
            book.rebalance(t, spot_bar.open, held.candles[t].open, pending)
            pending = None
        if held is not None and liquidated_at is None:
            mark = held.marks[t]
            level = book.liquidated_by(mark.high)
            if level is not None:
                book.liquidate(max(mark.open, level))
                liquidated_at = t
        spot_close = spot_bar.close if spot_bar is not None else last_spot_close
        last_spot_close = spot_close
        future_close = held.marks[t].close if held is not None else 0.0
        if t == hours[-1]:
            if book.short_qty:
                book._trade_short(-book.short_qty, held.candles[t].close)
            if book.spot_qty:
                book._trade_spot(-book.spot_qty, spot_close)
        equity = book.equity(spot_close, future_close)
        if equity <= 0 or not isfinite(equity):
            raise ValueError("basis account insolvent")
        curve.append(EquityPoint(t, equity, book.short_qty > 0))
        if book.short_qty:
            mark = held.marks[t]
            perp_equity = book.perp_equity(mark.close)
            max_leverage = max(max_leverage, book.short_qty * mark.close / perp_equity)
            max_margin_ratio = max(max_margin_ratio, book.short_qty * mark.high * config.assumed_mmr
                                   / max(book.perp_equity(mark.high), 1e-9))
            if perp_equity / (book.short_qty * mark.close) < config.emergency_margin_ratio and pending is None:
                pending = "emergency"
    final = curve[-1].equity
    if abs(book.spot_cash + book.perp_wallet - final) > 1e-6 or book.spot_qty > 1e-12 or book.short_qty:
        raise ValueError("basis account does not reconcile after exit")
    metrics = calculate_metrics(curve, [], config.initial_cash, "1h", max_margin_ratio)
    return dict(metrics=asdict(metrics), final_equity=final, fees=book.fees, slippage=book.slippage,
                liquidation_fee=book.liquidation_fee, liquidated_at_ms=liquidated_at, entries=entries,
                rebalances=book.rebalances, emergency_rebalances=sum(r["reason"] == "emergency" for r in book.rebalances),
                maximum_contract_leverage=max_leverage, maximum_margin_ratio=max_margin_ratio,
                invested_hours=sum(p.invested for p in curve), spot_outage_hours=sorted(missing))
