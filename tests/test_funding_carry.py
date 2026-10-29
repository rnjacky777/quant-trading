from datetime import datetime, timezone

import pytest

from app.backtest.funding_carry import CarryConfig, run_funding_carry
from app.data.models import Candle, FundingRate, MarkPriceCandle

H = 3600000
START = int(datetime(2024, 1, 31, 20, tzinfo=timezone.utc).timestamp() * 1000)  # crosses a month start


def tape(prices, *, spot_offset=0.0):
    perp = [Candle("binance-usdm", "BTC/USDT", "1h", START + i * H, p, p, p, p, 1) for i, p in enumerate(prices)]
    marks = [MarkPriceCandle(c.exchange, c.symbol, c.timestamp_ms, c.open, c.high, c.low, c.close, timeframe="1h") for c in perp]
    spot = {c.timestamp_ms: Candle("binance", "BTC/USDT", "1h", c.timestamp_ms, *(4 * [c.open + spot_offset]), 1) for c in perp}
    return perp, marks, spot


def free(**kwargs):
    return CarryConfig(0, 0, 0, 0, **kwargs)


def test_hedge_is_price_neutral_without_costs_or_funding():
    perp, marks, spot = tape([100, 130, 70, 100, 160, 90])
    result = run_funding_carry(perp, marks, [], spot, free())
    assert result["final_equity"] == pytest.approx(10000)
    assert all(e == pytest.approx(10000) for _, e in result["equity_curve"])
    reasons = [r["reason"] for r in result["rebalances"]]
    assert reasons[0] == "entry" and "emergency" in reasons


def test_short_receives_positive_funding_on_two_thirds_notional():
    perp, marks, spot = tape([100] * 10)
    funding = [FundingRate("binance-usdm", "BTC/USDT", START + 8 * H, .001, 100)]
    result = run_funding_carry(perp, marks, funding, spot, free())
    assert result["funding_income"] == pytest.approx(10000 * 2 / 3 * .001)
    assert result["final_equity"] == pytest.approx(10000 + 10000 * 2 / 3 * .001)
    negative = [FundingRate("binance-usdm", "BTC/USDT", START + 8 * H, -.001, 100)]
    assert run_funding_carry(perp, marks, negative, spot, free())["final_equity"] < 10000


def test_costs_are_charged_on_both_legs_entry_rebalance_and_exit():
    perp, marks, spot = tape([100] * 6)
    result = run_funding_carry(perp, marks, [], spot, CarryConfig(5, 5, 10, 5))
    notional = 10000 * 2 / 3
    # entry and exit on both legs; the month-start rebalance trades only the residual size change.
    assert result["fees"] == pytest.approx(2 * notional * (5 + 10) / 10000, rel=.01)
    assert result["final_equity"] < 10000 - result["fees"] - result["slippage"] + 1e-6


def test_rally_triggers_emergency_rebalance_before_liquidation():
    prices = [100] + [100 * 1.2 ** i for i in range(1, 6)]
    perp, marks, spot = tape(prices)
    result = run_funding_carry(perp, marks, [], spot, free())
    assert result["emergency_rebalances"] >= 1 and result["liquidated_at_ms"] is None
    assert result["final_equity"] == pytest.approx(10000)


def test_gap_rally_without_rebalance_time_is_liquidated_and_flagged():
    perp, marks, spot = tape([100, 100, 100])
    marks[1] = MarkPriceCandle("binance-usdm", "BTC/USDT", marks[1].timestamp_ms, 100, 160, 100, 100, timeframe="1h")
    result = run_funding_carry(perp, marks, [], spot, free())
    assert result["liquidated_at_ms"] == marks[1].timestamp_ms and result["liquidation_fee"] > 0


def test_only_registered_spot_outage_is_tolerated_and_rebalance_waits():
    perp, marks, spot = tape([100] * 8)
    month_start = START + 4 * H
    del spot[month_start]
    with pytest.raises(ValueError, match="registered outages"):
        run_funding_carry(perp, marks, [], spot, free())
    result = run_funding_carry(perp, marks, [], spot, free(), known_spot_outages=frozenset({month_start}))
    assert [r["timestamp_ms"] for r in result["rebalances"]] == [START, month_start + H]
    assert result["spot_outage_hours"] == [month_start]


def test_drift_band_rebalances_after_spot_value_drifts_past_band():
    perp, marks, spot = tape([100, 104, 104, 110, 110, 110])
    result = run_funding_carry(perp, marks, [], spot, free(target_fraction=.43, drift_band=.05))
    drift = [r for r in result["rebalances"] if r["reason"] == "drift"]
    assert [r["timestamp_ms"] for r in drift] == [START + 4 * H]
    assert drift[0]["quantity"] == pytest.approx(.43 * 10000 / 110)
    assert all(r["reason"] != "drift" for r in run_funding_carry(perp, marks, [], spot, free(target_fraction=.43))["rebalances"])


def test_funding_pause_stays_flat_until_recent_funding_is_positive():
    perp, marks, spot = tape([100] * 12)
    history = [FundingRate("binance-usdm", "BTC/USDT", START - k * 8 * H, -.0001, 100) for k in range(1, 4)]
    flat = run_funding_carry(perp, marks, [], spot, free(pause_funding_events=3), funding_history=history)
    assert flat["rebalances"] == [] and flat["final_equity"] == pytest.approx(10000)
    positive = [FundingRate("binance-usdm", "BTC/USDT", START + 2 * H, .002, 100)]
    resumed = run_funding_carry(perp, marks, positive, spot, free(pause_funding_events=3), funding_history=history)
    assert [r["reason"] for r in resumed["rebalances"]][0] == "entry"
    assert resumed["rebalances"][0]["timestamp_ms"] == START + 2 * H  # published at the hour, usable then


def test_funding_pause_flattens_both_legs_when_funding_turns_negative():
    perp, marks, spot = tape([100, 100, 120, 120, 120, 120])
    history = [FundingRate("binance-usdm", "BTC/USDT", START - k * 8 * H, .001, 100) for k in (1, 2)]
    negative = [FundingRate("binance-usdm", "BTC/USDT", START + 2 * H, -.003, 120)]
    result = run_funding_carry(perp, marks, negative, spot, free(pause_funding_events=2), funding_history=history)
    reasons = [r["reason"] for r in result["rebalances"]]
    assert reasons[0] == "entry" and "pause" in reasons
    pause = next(r for r in result["rebalances"] if r["reason"] == "pause")
    assert pause["timestamp_ms"] == START + 2 * H and result["pauses"] == 1
    assert result["final_equity"] == pytest.approx(10000 + 10000 * 2 / 3 / 100 * 120 * -.003)
