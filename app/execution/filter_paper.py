"""Forward paper runner for the BTC spot 50-day filter (registration: 2026-10-30-btc-trend-filter-forward-paper.md).

Event-sourced: every decision, virtual fill and stop is an idempotent ledger event, and book state is
rebuilt from the ledger on each start. The signal is the backtest's own `wants_btc`. Never sends orders.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from math import floor
from pathlib import Path
from typing import Callable, Protocol

from app.backtest.trend_filter import wants_btc
from app.data.live_perpetual import BinanceUsdmPublicFeed, Quote, SPOT_URL
from app.execution.paper_ledger import PaperLedger

DAY_MS = 86400000
WINDOW = 50
QTY_STEP = 0.00001
MIN_NOTIONAL = 5.0
KLINE_SETTLE_MS = 3000
QUOTE_MAX_AGE_MS = 5000
CLOCK_SKEW_MS = 1000
LATE_MS = 2 * 3600000
ACCOUNT_STOP = .30
COSTS = {"primary": (10, 5), "10/10": (10, 10), "doubled": (20, 10), "stress": (30, 15)}


class SpotDailyFeed(Protocol):
    def server_time(self) -> int: ...
    def closed_daily(self) -> dict[int, float]: ...
    def quote(self) -> Quote: ...


class BinanceSpotDailyFeed:
    """Public Binance spot endpoints only; no keys."""

    def __init__(self) -> None:
        self._http = BinanceUsdmPublicFeed()

    def server_time(self) -> int:
        return int(self._http._get("/api/v3/time", SPOT_URL)["serverTime"])

    def closed_daily(self) -> dict[int, float]:
        rows = self._http._get("/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=200", SPOT_URL)
        server = self.server_time()
        return {int(r[0]): float(r[4]) for r in rows if int(r[6]) + KLINE_SETTLE_MS < server}

    def quote(self) -> Quote:
        return self._http.spot_quote()


@dataclass
class Book:
    cash: float
    btc: float = 0.0
    year_start: dict | None = None
    stopped_years: set | None = None


def utc_year(t: int) -> int:
    return datetime.fromtimestamp(t / 1000, timezone.utc).year


class FilterPaperRunner:
    def __init__(self, run_dir: Path, feed: SpotDailyFeed, clock: Callable[[], int], capital: float = 3000.0) -> None:
        self.ledger = PaperLedger(run_dir / "events.jsonl")
        self.feed, self.clock, self.capital = feed, clock, capital

    def books(self) -> dict[str, Book]:
        """Rebuild every book from the ledger."""
        books = {case: Book(self.capital, 0.0, {}, set()) for case in COSTS}
        for event in self.ledger.events:
            p = event.payload
            if event.type == "fill":
                book = books[p["book"]]
                book.cash += -p["notional"] - p["fee"] if p["side"] == "buy" else p["notional"] - p["fee"]
                book.btc += p["quantity"] if p["side"] == "buy" else -p["quantity"]
                book.btc = 0.0 if abs(book.btc) < 1e-12 else book.btc
            elif event.type == "year_start":
                books[p["book"]].year_start[p["year"]] = p["equity"]
            elif event.type == "stop":
                books[p["book"]].stopped_years.add(p["year"])
        return books

    def decisions(self) -> dict[int, bool]:
        return {e.payload["day_ms"]: e.payload["hold_btc"] for e in self.ledger.events if e.type == "decision"}

    def _incident(self, kind: str, now: int, detail: dict) -> str:
        self.ledger.append("incident", f"incident:{kind}:{now}", dict(kind=kind, **detail), now)
        return f"incident {kind}"

    def step(self) -> str:
        now, server = self.clock(), self.feed.server_time()
        if abs(now - server) > CLOCK_SKEW_MS:
            return self._incident("clock_skew", now, dict(local_ms=now, server_ms=server))
        day = server // DAY_MS * DAY_MS
        if f"decision:{day}" in self.ledger:
            return "already decided"
        closes = self.feed.closed_daily()
        days = [day - k * DAY_MS for k in range(WINDOW, 0, -1)]
        if any(t not in closes for t in days):
            return self._incident("bar_missing", now, dict(day_ms=day, missing=[t for t in days if t not in closes]))
        first = min(self.decisions(), default=day)
        if any(t not in self.decisions() for t in range(first, day, DAY_MS)):
            self._incident("decision_gap", now, dict(day_ms=day, missing=[t for t in range(first, day, DAY_MS)
                                                                         if t not in self.decisions()]))
        quote = self.feed.quote()
        if server - quote.exchange_ms > QUOTE_MAX_AGE_MS:
            return self._incident("quote_stale", now, dict(day_ms=day, age_ms=server - quote.exchange_ms))
        history = [closes[t] for t in days]
        hold = wants_btc(history, WINDOW)
        previous_close = history[-1]
        self.ledger.append("decision", f"decision:{day}", dict(
            day_ms=day, hold_btc=hold, previous_close=previous_close, mean=sum(history) / WINDOW,
            delay_ms=server - day, late=server - day > LATE_MS, bid=quote.bid, ask=quote.ask, quote_ms=quote.exchange_ms), now)
        year = utc_year(day)
        for case, book in self.books().items():
            fee_bps, slip_bps = COSTS[case]
            if year not in book.year_start:
                self.ledger.append("year_start", f"year_start:{year}:{case}", dict(
                    book=case, year=year, equity=book.cash + book.btc * previous_close), now)
                book.year_start[year] = book.cash + book.btc * previous_close
            if year in book.stopped_years:
                continue
            stop = book.btc and book.cash + book.btc * previous_close <= book.year_start[year] * (1 - ACCOUNT_STOP)
            if stop:
                self.ledger.append("stop", f"stop:{year}:{case}", dict(book=case, year=year, day_ms=day), now)
            if book.btc and (stop or not hold):
                price = quote.bid * (1 - slip_bps / 10000)
                notional = book.btc * price
                self._fill(day, case, "sell", book.btc, price, notional, notional * fee_bps / 10000, now)
            elif hold and not book.btc and not stop:
                price = quote.ask * (1 + slip_bps / 10000)
                quantity = floor(book.cash / (price * (1 + fee_bps / 10000)) / QTY_STEP) * QTY_STEP
                if quantity * price >= MIN_NOTIONAL:
                    notional = quantity * price
                    self._fill(day, case, "buy", quantity, price, notional, notional * fee_bps / 10000, now)
        mid = (quote.bid + quote.ask) / 2
        self.ledger.append("mark", f"mark:{day}", dict(day_ms=day, mid=mid, equity={
            case: book.cash + book.btc * mid for case, book in self.books().items()}), now)
        return f"decided {'BTC' if hold else 'USDT'}"

    def _fill(self, day: int, case: str, side: str, quantity: float, price: float, notional: float, fee: float, now: int) -> None:
        self.ledger.append("fill", f"fill:{day}:{case}", dict(book=case, day_ms=day, side=side, quantity=quantity,
                                                              price=price, notional=notional, fee=fee), now)
