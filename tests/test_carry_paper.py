from datetime import datetime, timezone

import pytest

from app.backtest.funding_carry import CarryConfig, run_funding_carry
from app.data.live_perpetual import FeedError, Quote
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.execution.carry_paper import PaperCarryBook
from app.execution.paper_runner import HOUR_MS, PaperRunner, RunConfig, frozen_carry_books
from tests.test_perpetual_paper import Clock, Feed, books

H = HOUR_MS
START = int(datetime(2024, 1, 31, 20, tzinfo=timezone.utc).timestamp() * 1000)


def quote(price, t):
    return Quote(price, price, price, t, t, t)


def replay(perp, marks, funding, spot, config):
    """Drive the paper book with research prices: rebalance at opens, value at closes."""
    book = PaperCarryBook(config)
    for i, candle in enumerate(perp):
        t = candle.timestamp_ms
        events = [f for f in funding if t <= f.timestamp_ms < t + H]
        book.settle_funding([f for f in events if f.timestamp_ms <= t])
        book.on_decision(t, quote(spot[t].open, t), quote(candle.open, t), first_hour=i == 0)
        book.settle_funding([f for f in events if f.timestamp_ms > t])
        if i == len(perp) - 1:
            book.close_all(t, quote(spot[t].close, t), quote(candle.close, t))
        else:
            book.on_close(t, spot[t].close, marks[i].close)
    return book


def tape(prices):
    perp = [Candle("binance-usdm", "BTC/USDT", "1h", START + i * H, p, p, p, p, 1) for i, p in enumerate(prices)]
    marks = [MarkPriceCandle(c.exchange, c.symbol, c.timestamp_ms, c.open, c.high, c.low, c.close, timeframe="1h") for c in perp]
    spot = {c.timestamp_ms: Candle("binance", "BTC/USDT", "1h", c.timestamp_ms, *(4 * [c.open * 1.0002]), 1) for c in perp}
    return perp, marks, spot


@pytest.mark.parametrize("rules", [dict(), dict(target_fraction=.43, drift_band=.05)])
def test_paper_carry_matches_research_ledger_under_research_prices(rules):
    perp, marks, spot = tape([100, 104, 111, 130, 128, 140, 120, 125])
    funding = [FundingRate("binance-usdm", "BTC/USDT", START + 4 * H, .0004, 128),
               FundingRate("binance-usdm", "BTC/USDT", START + 6 * H + 2, -.0001, 120)]
    config = CarryConfig(5, 5, 10, 5, **rules)
    research = run_funding_carry(perp, marks, funding, spot, config)
    paper = replay(perp, marks, funding, spot, config)
    assert paper.points[-1][1] == pytest.approx(research["final_equity"], abs=1e-9)
    assert [(r["timestamp_ms"], r["reason"]) for r in paper.book.rebalances] == \
        [(r["timestamp_ms"], r["reason"]) for r in research["rebalances"]]
    assert paper.book.funding == pytest.approx(research["funding_income"])


def test_quote_fills_buy_spot_at_ask_and_sell_perp_at_bid():
    book = PaperCarryBook(CarryConfig(5, 5, 10, 5))
    book.on_decision(START, Quote(99, 101, 100, START, START), Quote(98, 102, 100, START, START), first_hour=True)
    b = book.book
    assert b.spot_qty == pytest.approx(b.short_qty) and b.spot_qty > 0
    assert b.short_entry == pytest.approx(98 * .9995)
    assert book.hedge_issues() == []
    with pytest.raises(ValueError):
        book.settle_funding([FundingRate("x", "BTC/USDT", 1, .1, 1)] * 2)


class SpotFeed(Feed):
    def __init__(self, *args, spot_down=lambda t: False, **kwargs):
        super().__init__(*args, **kwargs)
        self.spot_down = spot_down

    def spot_quote(self):
        if self.spot_down(self.clock.now):
            raise FeedError("spot down")
        p = self.price(self.clock.now) * 1.0001
        return Quote(p - .01, p + .01, p, self.clock.now, self.clock.now, self.clock.now)


def runner(tmp_path, feed, clock, hours=6):
    start = 1000 * H
    config = RunConfig("carry-test", "rehearsal", start, start + hours * H, poll_seconds=300)
    carry = {k: v for k, v in frozen_carry_books().items() if k.endswith(":5/5")}
    return PaperRunner(tmp_path, feed, clock, {"test": True}, config, hashes=lambda: {"x": "1"},
                       books=books({}), carry_books=carry)


def test_runner_holds_hedged_carry_collects_funding_and_restores(tmp_path):
    clock = Clock(1000 * H - H)
    run = runner(tmp_path, SpotFeed(clock, lambda t: 100.0), clock, hours=10)
    result = run.run()
    assert result["reason"] == "end_of_window" and result["spot_quote"] is not None
    for name, carry in run.carry_books.items():
        assert carry.closed and carry.book.rebalances[0]["reason"] == "entry"
        assert carry.book.funding > 0
        assert carry.points[-1][1] == pytest.approx(carry.book.spot_cash + carry.book.perp_wallet)
    assert not [i for i in run.incidents if i["kind"].startswith("carry")]
    again = runner(tmp_path, SpotFeed(clock, lambda t: 100.0), clock, hours=10)
    assert again.run() == result
    assert {k: c.points for k, c in again.carry_books.items()} == {k: c.points for k, c in run.carry_books.items()}


def test_spot_outage_defers_carry_entry_without_blocking_trend(tmp_path):
    clock = Clock(1000 * H - H)
    feed = SpotFeed(clock, lambda t: 100.0, spot_down=lambda t: t < 1000 * H + 30 * 60000)
    run = runner(tmp_path, feed, clock, hours=3)
    run.run()
    assert any(i["kind"] == "carry_rebalance_deferred" for i in run.incidents)
    decisions = [e.payload for e in run.ledger.events if e.type == "decision"]
    assert decisions[0]["allow_entries"] and not decisions[0]["carry_quotes_ok"]
    entry = next(iter(run.carry_books.values())).book.rebalances[0]
    assert entry["reason"] == "entry" and entry["timestamp_ms"] == 1000 * H + H
