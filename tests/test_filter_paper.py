from datetime import datetime, timezone

import pytest

from app.backtest.trend_filter import wants_btc
from app.data.live_perpetual import Quote
from app.execution.filter_paper import DAY_MS, FilterPaperRunner

DAY = int(datetime(2026, 11, 2, tzinfo=timezone.utc).timestamp() * 1000)


class FakeFeed:
    def __init__(self, closes, now, bid=100.0, ask=100.1, quote_age=0):
        self.closes, self.now, self.bid, self.ask, self.quote_age = closes, now, bid, ask, quote_age

    def server_time(self):
        return self.now

    def closed_daily(self):
        return {t: c for t, c in self.closes.items() if t + DAY_MS <= self.now}

    def quote(self):
        return Quote(self.bid, self.ask, self.bid, self.now - self.quote_age, self.now)


def rising(end_day, n=60, start=50.0):
    return {end_day - (n - i) * DAY_MS: start + i for i in range(n)}


def runner(tmp_path, feed):
    return FilterPaperRunner(tmp_path, feed, lambda: feed.now)


def test_buys_on_uptrend_with_backtest_signal_and_is_idempotent(tmp_path):
    closes = rising(DAY)
    feed = FakeFeed(closes, DAY + 60000)
    r = runner(tmp_path, feed)
    assert r.step() == "decided BTC"
    history = [closes[DAY - k * DAY_MS] for k in range(50, 0, -1)]
    assert r.decisions()[DAY] == wants_btc(history, 50) is True
    assert r.step() == "already decided"
    restarted = runner(tmp_path, feed)
    books = restarted.books()
    primary = books["primary"]
    assert primary.btc > 0 and primary.cash >= 0
    # Fill at ask plus 5 bps slippage and 10 bps fee, quantity floored to 0.00001.
    price = 100.1 * 1.0005
    assert primary.cash == pytest.approx(3000 - primary.btc * price * 1.001)
    assert sum(e.type == "fill" for e in restarted.ledger.events) == 4


def test_sells_when_close_drops_below_mean_and_stays_flat(tmp_path):
    closes = rising(DAY)
    feed = FakeFeed(closes, DAY + 60000)
    r = runner(tmp_path, feed)
    r.step()
    closes[DAY] = 10.0
    feed.now = DAY + DAY_MS + 60000
    assert r.step() == "decided USDT"
    assert all(b.btc == 0 for b in r.books().values())
    assert r.books()["primary"].cash < 3000


def test_missing_bar_or_stale_quote_defers_without_decision(tmp_path):
    closes = rising(DAY)
    del closes[DAY - 3 * DAY_MS]
    r = runner(tmp_path, FakeFeed(closes, DAY + 60000))
    assert r.step() == "incident bar_missing" and r.decisions() == {}
    stale = runner(tmp_path / "s", FakeFeed(rising(DAY), DAY + 60000, quote_age=6000))
    assert stale.step() == "incident quote_stale" and stale.decisions() == {}


def test_account_stop_sells_and_blocks_rebuy_for_the_year(tmp_path):
    closes = rising(DAY)
    feed = FakeFeed(closes, DAY + 60000)
    r = runner(tmp_path, feed)
    r.step()
    # Price collapses but stays above the falling mean only via a single huge close: force the stop path.
    closes[DAY] = 60.0  # previous close: equity about 3000 * 60 / 109 < 70%
    feed.now, feed.bid, feed.ask = DAY + DAY_MS + 60000, 60.0, 60.1
    r.step()
    assert any(e.type == "stop" for e in r.ledger.events)
    assert all(b.btc == 0 for b in r.books().values())
    closes[DAY + DAY_MS] = 500.0
    feed.now = DAY + 2 * DAY_MS + 60000
    r.step()
    assert all(b.btc == 0 for b in r.books().values())
