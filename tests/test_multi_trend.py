from datetime import datetime, timezone

import numpy as np
import pytest

from app.backtest.multi_trend import DAY_MS, TrendConfig, run_multi_trend, target_weights

START = int(datetime(2024, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)  # a Monday


def series(prices):
    begin = START - 70 * DAY_MS
    return {begin + i * DAY_MS: (p, p * 1.01, p * .99, p) for i, p in enumerate(prices)}


def noisy(drift, n, seed):
    rng = np.random.default_rng(seed)
    return list(100 * np.cumprod(1 + drift + rng.normal(0, .02, n)))


def test_signs_follow_lookback_return_and_vol_target_scales_portfolio():
    up, down = noisy(.01, 61, 1), noisy(-.01, 61, 2)
    config = TrendConfig(30, 0, 0, coin_cap=10, gross_cap=10)
    w = target_weights({"UP": up, "DOWN": down}, config)
    assert w["UP"] > 0 and w["DOWN"] < 0
    r = np.vstack([np.diff(down) / down[:-1], np.diff(up) / up[:-1]])  # sorted symbol order: DOWN, UP
    vec = np.array([w["DOWN"], w["UP"]])
    assert float(np.sqrt(vec @ (np.cov(r, ddof=1) * 365) @ vec)) == pytest.approx(.20, rel=1e-6)


def test_caps_limit_single_coin_and_gross_exposure():
    calm = list(100 * np.cumprod(1 + .001 + np.random.default_rng(3).normal(0, .0005, 61)))
    w = target_weights({"CALM": calm}, TrendConfig(30, 0, 0))
    assert w == {"CALM": pytest.approx(.30)}


def test_long_position_profits_from_trend_and_pays_positive_funding():
    prices = [100 * 1.01 ** i for i in range(100)]
    bars = {"BTCUSDT": series(prices)}
    config = TrendConfig(30, 0, 0, coin_cap=1.0)
    free = run_multi_trend(bars, {}, {"2024-04": ["BTCUSDT"]}, config, START, START + 7 * DAY_MS)
    assert free["final_equity"] > 10000 and free["rebalances"] == 1
    funded = run_multi_trend(bars, {"BTCUSDT": [(START + DAY_MS + 8 * 3600000, .001)]}, {"2024-04": ["BTCUSDT"]},
                             config, START, START + 7 * DAY_MS)
    assert funded["funding_paid"] > 0 and funded["final_equity"] < free["final_equity"]


def test_account_stop_flattens_and_stays_out():
    prices = [100 * 1.01 ** i for i in range(71)] + [100 * 1.01 ** 70 * .5 ** k for k in range(1, 30)]
    bars = {"BTCUSDT": series(prices)}
    result = run_multi_trend(bars, {}, {"2024-04": ["BTCUSDT"]}, TrendConfig(30, 0, 0, coin_cap=1.0, gross_cap=2.0,
                             vol_target=5.0), START, START + 20 * DAY_MS)
    assert result["account_stop_at_ms"] is not None
    assert result["invested_days"] < 20
