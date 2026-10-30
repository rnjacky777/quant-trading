from datetime import datetime, timezone

import pytest

from app.backtest.trend_filter import DAY_MS, FilterConfig, run_trend_filter, wants_btc

START = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def bars(prices, warm):
    begin = START - warm * DAY_MS
    return {begin + i * DAY_MS: (p, p, p, p) for i, p in enumerate(prices)}


def test_signal_needs_full_window_and_close_above_mean():
    assert not wants_btc([1, 2, 3], 4)
    assert wants_btc([1, 2, 3, 4], 4) and not wants_btc([4, 3, 2, 1], 4)


def test_holds_through_uptrend_and_exits_after_break():
    prices = [100 + i for i in range(10)] + [110 + i for i in range(10)] + [80] * 10
    result = run_trend_filter(bars(prices, 10), FilterConfig(5, 0, 0), START, START + 20 * DAY_MS)
    # Enters on day 0 at 110, exits on the open after the first close below the mean (the drop to 80).
    assert result["trades"] == 2 and result["final_equity"] == pytest.approx(10000 * 80 / 110)


def test_no_history_means_cash_and_costs_are_charged():
    prices = [100.0] * 30
    flat = run_trend_filter(bars(prices, 0), FilterConfig(50, 10, 5), START, START + 30 * DAY_MS)
    assert flat["trades"] == 0 and flat["final_equity"] == 10000
    rising = [100 + i for i in range(40)]
    paid = run_trend_filter(bars(rising, 10), FilterConfig(5, 10, 5), START, START + 30 * DAY_MS)
    assert paid["fees"] > 0 and paid["slippage"] > 0
