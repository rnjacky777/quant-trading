"""Multi-coin funding carry research: monthly top-K funding selection inside a point-in-time liquid universe.

Rules are frozen in docs/research/2026-10-30-multi-coin-carry-design.md. Each selected coin is an
independent `CarryBook` slot with its own margin; transfers between slots are assumed free at month
starts. Research only; not a paper source.
"""
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from math import isfinite

from app.backtest.funding_carry import CarryBook, CarryConfig, HOUR_MS
from app.backtest.metrics import calculate_metrics
from app.backtest.models import EquityPoint

LOOKBACK_MS = 30 * 24 * HOUR_MS
MAJORS = frozenset({"BTCUSDT", "ETHUSDT"})


@dataclass(frozen=True)
class FundingEvent:
    """Duck-typed for `CarryBook.apply_funding`; `FundingRate` only accepts the platform's BTC/ETH symbols."""
    timestamp_ms: int
    rate: float
    mark_price: float


@dataclass(frozen=True)
class CoinTape:
    """Hourly OHLC tuples keyed by open time; spot already multiplied by the perp/spot price factor."""
    symbol: str
    perp: dict[int, tuple[float, float, float, float]]
    marks: dict[int, tuple[float, float, float, float]]
    spot: dict[int, tuple[float, float, float, float]]
    funding: list[tuple[int, float]]

    def has(self, t: int) -> bool:
        return t in self.perp and t in self.marks and t in self.spot


def month_key(t: int) -> str:
    return datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m")


def is_month_start(t: int) -> bool:
    d = datetime.fromtimestamp(t / 1000, timezone.utc)
    return d.day == 1 and d.hour == 0


def select(tapes: dict[str, CoinTape], members: list[str], t: int, k: int) -> list[str]:
    """Top-k members by mean funding published in the previous 30 days; mean must be positive."""
    scores = {}
    for symbol in members:
        tape = tapes.get(symbol)
        if tape is None or not tape.has(t):
            continue
        rates = [r for when, r in tape.funding if t - LOOKBACK_MS <= when < t]
        if rates and sum(rates) / len(rates) > 0:
            scores[symbol] = sum(rates) / len(rates)
    return sorted(scores, key=lambda s: (-scores[s], s))[:k]


def coin_config(base: CarryConfig, symbol: str) -> CarryConfig:
    if symbol in MAJORS:
        return base
    return replace(base, perp_slippage_bps=2 * base.perp_slippage_bps, spot_slippage_bps=2 * base.spot_slippage_bps)


def run_multi_carry(tapes: dict[str, CoinTape], universe: dict[str, list[str]], base: CarryConfig, k: int,
                    start_ms: int, end_ms: int, known_spot_outages: frozenset[int] = frozenset()) -> dict:
    """known_spot_outages: exchange-wide spot outage hours; no spot trading, valuation keeps the previous close."""
    hours = range(start_ms, end_ms, HOUR_MS)
    reserve = base.initial_cash
    books: dict[str, CarryBook] = {}
    pending: dict[str, str] = {}
    events: dict[str, dict[int, list[FundingEvent]]] = {}
    for symbol, tape in tapes.items():
        bucket = events.setdefault(symbol, {})
        for when, rate in tape.funding:
            hour = when // HOUR_MS * HOUR_MS
            mark = tape.marks.get(hour, tape.perp.get(hour, (0,)))[0]
            bucket.setdefault(hour, []).append(FundingEvent(when, rate, mark))
    curve = [EquityPoint(start_ms - HOUR_MS, base.initial_cash, False)]
    log = dict(selections=[], liquidations=[], data_exits=[], emergency=0)
    funding_income = fees = 0.0
    max_margin_ratio = 0.0
    last_close: dict[str, tuple[float, float]] = {}

    def outage(symbol: str, t: int) -> bool:
        tape = tapes[symbol]
        return t in known_spot_outages and t not in tape.spot and t in tape.perp and t in tape.marks

    def spot_close(symbol: str, t: int) -> float:
        return last_close[symbol][0] if outage(symbol, t) else tapes[symbol].spot[t][3]

    def close_book(symbol: str, spot_price: float, perp_price: float, config: CarryConfig | None = None) -> None:
        nonlocal reserve, fees, funding_income
        book = books.pop(symbol)
        if config is not None:
            book.config = config
        if book.short_qty:
            book._trade_short(-book.short_qty, perp_price)
        if book.spot_qty:
            book._trade_spot(-book.spot_qty, spot_price)
        reserve += book.spot_cash + book.perp_wallet
        fees += book.fees
        funding_income += book.funding
        pending.pop(symbol, None)

    for t in hours:
        last = t == hours[-1]
        for symbol, book in books.items():
            for event in events[symbol].get(t, []) if tapes[symbol].has(t) or outage(symbol, t) else []:
                if event.timestamp_ms <= t:
                    book.apply_funding(event)
        rotation = (t == start_ms or is_month_start(t)) and not last
        if rotation:
            chosen = select(tapes, universe.get(month_key(t), []), t, k)
            log["selections"].append(dict(timestamp_ms=t, chosen=chosen))
            for symbol in [s for s in books if s not in chosen]:
                # Hourly data is stored only for universe months, so a rotated-out coin may lack this bar.
                tape = tapes[symbol]
                spot_open, perp_open = (tape.spot[t][0], tape.perp[t][0]) if tape.has(t) else last_close[symbol]
                close_book(symbol, spot_open, perp_open)
            total = reserve + sum(b.equity(tapes[s].spot[t][0], tapes[s].perp[t][0]) for s, b in books.items())
            slot = total / k
            for symbol in chosen:
                book = books.get(symbol)
                if book is None:
                    book = books[symbol] = CarryBook(coin_config(base, symbol))
                transfer = slot - book.equity(tapes[symbol].spot[t][0], tapes[symbol].perp[t][0])
                book.spot_cash += transfer
                reserve -= transfer
                book.rebalance(t, tapes[symbol].spot[t][0], tapes[symbol].perp[t][0], "selection")
                pending.pop(symbol, None)
        for symbol in list(books):
            if not tapes[symbol].has(t) and not outage(symbol, t):
                spot_close_, perp_close = last_close[symbol]
                cfg = books[symbol].config
                close_book(symbol, spot_close_, perp_close, replace(cfg, perp_slippage_bps=2 * cfg.perp_slippage_bps,
                                                                    spot_slippage_bps=2 * cfg.spot_slippage_bps))
                log["data_exits"].append(dict(timestamp_ms=t, symbol=symbol))
        for symbol, reason in list(pending.items()):
            if symbol in books and outage(symbol, t):
                continue
            if symbol in books:
                books[symbol].rebalance(t, tapes[symbol].spot[t][0], tapes[symbol].perp[t][0], reason)
            pending.pop(symbol)
        for symbol, book in books.items():
            for event in events[symbol].get(t, []):
                if event.timestamp_ms > t:
                    book.apply_funding(event)
        for symbol in list(books):
            book, tape = books[symbol], tapes[symbol]
            level = book.liquidated_by(tape.marks[t][1])
            if level is not None:
                book.liquidate(max(tape.marks[t][0], level))
                log["liquidations"].append(dict(timestamp_ms=t, symbol=symbol))
                close_book(symbol, spot_close(symbol, t), tape.perp[t][3])
        for symbol, book in books.items():
            last_close[symbol] = (spot_close(symbol, t), tapes[symbol].perp[t][3])
        if last:
            for symbol in list(books):
                close_book(symbol, tapes[symbol].spot[t][3], tapes[symbol].perp[t][3])
        equity = reserve + sum(b.equity(spot_close(s, t), tapes[s].marks[t][3]) for s, b in books.items())
        if equity <= 0 or not isfinite(equity):
            raise ValueError("multi-carry account insolvent")
        curve.append(EquityPoint(t, equity, bool(books)))
        for symbol, book in books.items():
            mark = tapes[symbol].marks[t]
            perp_equity = book.perp_equity(mark[3])
            max_margin_ratio = max(max_margin_ratio, book.short_qty * mark[1] * base.assumed_mmr
                                   / max(book.perp_equity(mark[1]), 1e-9))
            if book.short_qty and perp_equity / (book.short_qty * mark[3]) < base.emergency_margin_ratio:
                pending.setdefault(symbol, "emergency")
                log["emergency"] += 1
    if books or abs(reserve - curve[-1].equity) > 1e-6:
        raise ValueError("multi-carry account does not reconcile after exit")
    metrics = calculate_metrics(curve, [], base.initial_cash, "1h", max_margin_ratio)
    return dict(metrics=asdict(metrics), final_equity=curve[-1].equity, funding_income=funding_income, fees=fees,
                maximum_margin_ratio=max_margin_ratio, invested_hours=sum(p.invested for p in curve), **log)
