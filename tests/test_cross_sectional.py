import numpy as np

from app.backtest import multi_trend
from app.backtest.cross_sectional import cross_sectional_weights, run_cross_sectional
from app.backtest.multi_trend import TrendConfig


def path(drift, seed):
    rng = np.random.default_rng(seed)
    return list(100 * np.cumprod(1 + drift + rng.normal(0, .01, 61)))


def test_longs_strongest_shorts_weakest_and_skips_middle():
    closes = {f"C{i}": path(.004 * (i - 5), i) for i in range(10)}
    w = cross_sectional_weights(closes, TrendConfig(14, 0, 0, coin_cap=10, gross_cap=10))
    assert {s for s, x in w.items() if x > 0} == {"C6", "C7", "C8", "C9"}
    assert {s for s, x in w.items() if x < 0} == {"C0", "C1", "C2", "C3"}


def test_too_few_coins_means_no_positions():
    closes = {f"C{i}": path(.001 * i, i) for i in range(7)}
    assert cross_sectional_weights(closes, TrendConfig(14, 0, 0)) == {}


def test_engine_rule_is_restored_after_run():
    run_cross_sectional({}, {}, {}, TrendConfig(14, 0, 0), 0, multi_trend.DAY_MS)
    assert multi_trend.target_weights.__name__ == "target_weights"


def test_funding_rule_shorts_crowded_and_longs_cheap_using_only_past_prints():
    from app.backtest.cross_sectional import funding_weights
    closes = {f"C{i}": path(0, i) for i in range(10)}
    t = 100 * multi_trend.DAY_MS
    funding = {f"C{i}": [(t - multi_trend.DAY_MS, .0001 * i), (t + 1, -1.0 if i == 9 else 0.0)] for i in range(10)}
    w = funding_weights(funding)(closes, TrendConfig(7, 0, 0, coin_cap=10, gross_cap=10), t)
    assert {s for s, x in w.items() if x < 0} == {"C6", "C7", "C8", "C9"}
    assert {s for s, x in w.items() if x > 0} == {"C0", "C1", "C2", "C3"}
