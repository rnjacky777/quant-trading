from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.data.live_perpetual import BinanceUsdmPublicFeed, FeedError, MarkSnapshot, Quote
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.execution.paper_ledger import LedgerCorrupted, PaperLedger
from app.execution.paper_replay import replay_research_fills
from app.execution.paper_runner import HOUR_MS, WARMUP_HOURS, PaperRunner, RunConfig, frozen_books
from app.execution.perpetual_paper import FillPrices, PaperPortfolioBook
from app.monitoring.paper_checks import StopRule, reconcile
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.base import Action
from app.strategies.directional_intraday import DirectionalSignal

START = 1000 * HOUR_MS  # divisible by 8h so funding settles at boundaries
MANIFEST = Path("docs/research/2026-10-29-forward-paper-manifest.json")


class Scripted:
    """Signals keyed by the last completed bar timestamp; stop at a fixed distance."""
    name = "scripted"

    def __init__(self, plan: dict[int, int], distance: float = 5, exit_after: set[int] = frozenset()):
        self.plan, self.distance, self.exit_after = plan, distance, exit_after

    def generate(self, candles):
        last = candles[-1]
        d = self.plan.get(last.timestamp_ms, 0)
        exiting = last.timestamp_ms in self.exit_after
        return DirectionalSignal("BTC/USDT", datetime.fromtimestamp(last.timestamp_ms / 1000, timezone.utc),
            Action.BUY if d == 1 else Action.SELL if d == -1 else Action.HOLD, abs(d), self.name,
            stop_loss_price=last.close - d * self.distance if d else None, direction=d,
            exit_long=exiting, exit_short=exiting)


def cfg(**kwargs):
    return replace(PerpetualResearchConfig(fee_bps=5, slippage_bps=5, funding_reserve=0, holding_hours=168), **kwargs)


def books(plan, **kwargs):
    def make(fee, slip):
        return PaperPortfolioBook([ResearchSleeve("a", Scripted(plan, **kwargs), cfg(fee_bps=fee, slippage_bps=slip))])
    return {"5/5": make(5, 5), "10/10": make(10, 10)}


class Clock:
    def __init__(self, now):
        self.now = now

    def now_ms(self):
        return self.now

    def sleep(self, seconds):
        self.now += int(seconds * 1000)


class Feed:
    def __init__(self, clock, price, *, bar_delay_ms=1000, quote_down=lambda t: False, stale_ms=0,
                 funding_available=True, crash_at=None):
        self.clock, self.price, self.bar_delay_ms = clock, price, bar_delay_ms
        self.quote_down, self.stale_ms, self.funding_available, self.crash_at = quote_down, stale_ms, funding_available, crash_at

    def _check(self):
        if self.crash_at is not None and self.clock.now >= self.crash_at:
            raise KeyboardInterrupt("simulated process crash")

    def _bar(self, h):
        samples = [self.price(h + m * 60000) for m in range(60)]
        return Candle("binance-usdm", "BTC/USDT", "1h", h, samples[0], max(samples), min(samples), samples[-1], 1)

    def server_time(self):
        return self.clock.now

    def closed_hourly(self, since_ms):
        self._check()
        h = since_ms // HOUR_MS * HOUR_MS
        out = []
        while h + HOUR_MS + self.bar_delay_ms <= self.clock.now:
            out.append((self._bar(h), self.clock.now))
            h += HOUR_MS
        return out

    def quote(self):
        self._check()
        if self.quote_down(self.clock.now):
            raise FeedError("disconnected")
        p = self.price(self.clock.now)
        return Quote(p - .5, p + .5, p, self.clock.now - self.stale_ms, self.clock.now)

    def mark(self):
        self._check()
        if self.quote_down(self.clock.now):
            raise FeedError("disconnected")
        nxt = (self.clock.now // (8 * HOUR_MS) + 1) * 8 * HOUR_MS
        return MarkSnapshot(self.price(self.clock.now), .0001, nxt, self.clock.now, self.clock.now)

    def funding(self, start_ms, end_ms):
        if not self.funding_available:
            return []
        first = (start_ms + 8 * HOUR_MS - 1) // (8 * HOUR_MS) * 8 * HOUR_MS
        return [FundingRate("binance-usdm", "BTC/USDT", t, .0001, self.price(t))
                for t in range(first, min(end_ms, self.clock.now) + 1, 8 * HOUR_MS)]


def runner(tmp_path, feed, clock, plan_books, hours=6, rule=StopRule(), hashes=lambda: {"x": "1"}):
    config = RunConfig("test-run", "rehearsal", START, START + hours * HOUR_MS, poll_seconds=300)
    return PaperRunner(tmp_path, feed, clock, {"test": True}, config, rule=rule, hashes=hashes, books=plan_books)


def flat(t):
    return 100.0


# ---- replay parity ----

def test_replay_matches_research_engine_with_stops_funding_and_exits():
    prices = [100 + (i % 7) * 3 - (i % 5) * 2 for i in range(60)]
    bars = [Candle("test", "BTC/USDT", "1h", i * HOUR_MS, p, p + 4, p - 4, p + 1, 1) for i, p in enumerate(prices)]
    marks = [MarkPriceCandle(c.exchange, c.symbol, c.timestamp_ms, c.open, c.high, c.low, c.close, timeframe="1h") for c in bars[1:]]
    funding = [FundingRate("test", "BTC/USDT", i * 8 * HOUR_MS, .0003 * (-1) ** i, 100) for i in range(1, 8)]
    plan = {i * HOUR_MS: (1 if i % 3 == 0 else -1 if i % 3 == 1 else 0) for i in range(60)}

    def sleeves():
        return [ResearchSleeve("a", Scripted(plan, 20, exit_after={i * HOUR_MS for i in range(0, 60, 4)}), cfg(holding_hours=5)),
                ResearchSleeve("b", Scripted({k: -v for k, v in plan.items()}, 6), cfg(holding_hours=9)),
                ResearchSleeve("c", Scripted(plan, 50), cfg(holding_hours=3))]
    research = PortfolioResearchEngine(sleeves(), PortfolioLimits(), directional_loss_guard=True).run(
        bars, evaluation_start_ms=HOUR_MS, marks=marks, funding=funding)
    paper = replay_research_fills(PaperPortfolioBook(sleeves()), bars, evaluation_start_ms=HOUR_MS, marks=marks, funding=funding)
    assert {t.exit_reason for t in research.trades} >= {"stop_loss", "time_limit", "signal"}
    assert serialize_result(paper) == serialize_result(research)


def test_quote_fills_buy_at_ask_sell_at_bid_with_adverse_slippage():
    book = PaperPortfolioBook([ResearchSleeve("a", Scripted({0: 1}), cfg())])
    bar = Candle("test", "BTC/USDT", "1h", 0, 100, 100, 100, 100, 1)
    signals = {"a": Scripted({0: 1}).generate([bar])}
    book.open_phase(hour_ms=HOUR_MS, history=[bar], signals=signals, trigger=100, prices=FillPrices(101, 99),
                    mark=100, fill_ms=HOUR_MS + 1500)
    lot = next(iter(book.book.values()))
    assert lot.position.entry_price == pytest.approx(101 * 1.0005)
    assert book.fills[0].fill_ms == HOUR_MS + 1500 and lot.position.entry_timestamp_ms == HOUR_MS
    book.close_all(hour_ms=2 * HOUR_MS, identity=bar, prices=FillPrices(103, 102), reason="end", fill_ms=2 * HOUR_MS)
    assert book.trades[0].exit_price == pytest.approx(102 * .9995)
    assert reconcile(book, 102) == []


# ---- ledger ----

def test_ledger_is_idempotent_and_detects_tampering_or_partial_records(tmp_path):
    path = tmp_path / "events.jsonl"
    ledger = PaperLedger(path)
    assert ledger.append("bar", "bar:1", {"x": 1}, 5) is not None
    assert ledger.append("bar", "bar:1", {"x": 2}, 6) is None
    ledger.append("bar", "bar:2", {"x": 3}, 7)
    assert [e.payload for e in PaperLedger(path).events] == [{"x": 1}, {"x": 3}]
    original = path.read_text()
    path.write_text(original.replace('"x":1', '"x":9'))
    with pytest.raises(LedgerCorrupted):
        PaperLedger(path)
    path.write_text(original + '{"seq":3')
    with pytest.raises(LedgerCorrupted):
        PaperLedger(path)


# ---- runner ----

def test_runner_records_decisions_reconciles_and_restores_identically(tmp_path):
    clock = Clock(START - HOUR_MS)
    price = lambda t: 100 + ((t // HOUR_MS) % 4)
    plan = {START: 1, START + HOUR_MS: -1}
    run = runner(tmp_path, Feed(clock, price), clock, books(plan))
    result = run.run()
    assert result["reason"] == "end_of_window"
    assert sorted(run.decided) == list(range(START, START + 6 * HOUR_MS, HOUR_MS))
    assert run.incidents == []
    assert [e.payload["timestamp_ms"] for e in run.ledger.events if e.type == "funding"] == [START]
    primary = run.books["5/5"]
    assert len(primary.trades) == 2 and not primary.book
    assert run.books["10/10"].cash < primary.cash
    assert all(reconcile(b, 100) == [] for b in run.books.values())
    events = len(run.ledger.events)
    restored = runner(tmp_path, Feed(clock, price), clock, books(plan))
    assert restored.run() == result and len(restored.ledger.events) == events
    assert serialize_result_trades(restored) == serialize_result_trades(run)


def serialize_result_trades(run):
    return {k: [t.position_id for t in b.trades] + [round(b.cash, 9)] for k, b in run.books.items()}


def test_crash_and_restart_never_redecides_or_backfills_missed_hours(tmp_path):
    clock = Clock(START - HOUR_MS)
    plan = {START + h * HOUR_MS: 1 for h in range(6)}
    with pytest.raises(KeyboardInterrupt):
        runner(tmp_path, Feed(clock, flat, crash_at=START + 2 * HOUR_MS + 600000), clock, books(plan)).run()
    clock.now = START + 4 * HOUR_MS + 1000
    run = runner(tmp_path, Feed(clock, flat), clock, books(plan))
    run.run()
    decisions = [e.payload["hour_ms"] for e in run.ledger.events if e.type == "decision"]
    assert len(decisions) == len(set(decisions))
    missed = sorted(int(i["key"]) for i in run.incidents if i["kind"] == "missed_hour")
    assert missed == [START + 3 * HOUR_MS]
    assert START + 3 * HOUR_MS not in run.decided


def test_stale_quote_blocks_entries_but_exits_still_fill(tmp_path):
    clock = Clock(START - HOUR_MS)
    plan = {START - HOUR_MS: 1}
    run = runner(tmp_path, Feed(clock, flat, stale_ms=0), clock, books(plan, exit_after={START + HOUR_MS}), hours=1)
    run.run()
    assert len(run.books["5/5"].trades) == 1
    clock2 = Clock(START - HOUR_MS)
    stale = runner(tmp_path / "stale", Feed(clock2, flat, stale_ms=10000), clock2, books(plan), hours=2)
    stale.run()
    assert not stale.books["5/5"].trades
    assert any(i["kind"] == "entries_blocked" and "quote_stale" in i["reasons"] for i in stale.incidents)
    assert any(a["reason"] == "data_quality_block" for a in stale.books["5/5"].admissions)


def test_late_bar_blocks_entries(tmp_path):
    clock = Clock(START - HOUR_MS)
    run = runner(tmp_path, Feed(clock, flat, bar_delay_ms=90000), clock, books({START - HOUR_MS: 1}), hours=1)
    run.run()
    assert not run.books["5/5"].trades
    blocked = next(i for i in run.incidents if i["kind"] == "entries_blocked")
    assert "bar_late" in blocked["reasons"]
    clock2 = Clock(START - HOUR_MS)
    missing = runner(tmp_path / "m", Feed(clock2, flat, bar_delay_ms=200000), clock2, books({START - HOUR_MS: 1}), hours=2)
    missing.run()
    assert not missing.books["5/5"].trades and START - HOUR_MS in missing.bars
    assert "bar_missing" in next(i for i in missing.incidents if i["kind"] == "entries_blocked")["reasons"]


def test_missing_funding_is_flagged_provisional_never_zero(tmp_path):
    clock = Clock(START - HOUR_MS)
    run = runner(tmp_path, Feed(clock, flat, funding_available=False), clock, books({START - HOUR_MS: -1}), hours=2)
    run.run()
    assert any(i["kind"] in {"funding_provisional", "funding_unavailable"} for i in run.incidents)
    clock2 = Clock(START + HOUR_MS - 60000)
    feed = Feed(clock2, flat, funding_available=False)
    later = runner(tmp_path / "b", feed, clock2, books({START + HOUR_MS * 8 - HOUR_MS: -1}), hours=9)
    later.run()
    provisional = [e.payload for e in later.ledger.events if e.type == "funding" and e.payload["provisional"]]
    assert provisional and provisional[0]["rate"] == .0001


def test_changed_paper_source_refuses_restart(tmp_path):
    clock = Clock(START - HOUR_MS)
    runner(tmp_path, Feed(clock, flat), clock, books({}), hours=1).run()
    with pytest.raises(ValueError, match="new registered run"):
        runner(tmp_path, Feed(clock, flat), clock, books({}), hours=1, hashes=lambda: {"x": "2"})


def test_intrabar_stop_fills_at_bid_and_stop_rule_terminates_all_books(tmp_path):
    clock = Clock(START - HOUR_MS)
    price = lambda t: 100.0 if t < START + 30 * 60000 else 90.0
    run = runner(tmp_path, Feed(clock, price), clock, books({START - HOUR_MS: 1}), hours=4,
                 rule=StopRule(minimum_return=-.0001))
    result = run.run()
    trade = run.books["5/5"].trades[0]
    assert trade.exit_reason == "stop_loss" and trade.exit_price == pytest.approx(89.5 * .9995)
    assert result["reason"] == "research_stop" and all(not b.book for b in run.books.values())
    assert sum(e.type == "tick" for e in run.ledger.events) == 1


def test_frozen_books_follow_manifest_without_order_capability():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    frozen = frozen_books(manifest)
    assert list(frozen) == ["5/5", "10/5", "10/10", "20/10"]
    for key, book in frozen.items():
        fee, slip = map(float, key.split("/"))
        assert all(s.config.risk_per_trade == .0025 and (s.config.fee_bps, s.config.slippage_bps) == (fee, slip)
                   for s in book.sleeves)
        assert book.limits == PortfolioLimits(**manifest["portfolio_limits"])
    with pytest.raises(ValueError):
        frozen_books({**manifest, "engine_flags": {**manifest["engine_flags"], "swing_long_signal_hold": True}})
    public = {n for n in dir(BinanceUsdmPublicFeed) if not n.startswith("_")}
    assert public == {"server_time", "closed_hourly", "quote", "mark", "funding"}
    assert WARMUP_HOURS == 243
