from datetime import datetime, timezone

import pytest

from app.backtest.funding_carry import CarryConfig
from app.backtest.multi_carry import CoinTape, run_multi_carry, select

H = 3600000
START = int(datetime(2024, 2, 1, tzinfo=timezone.utc).timestamp() * 1000)


def tape(symbol, hours, price=100.0, funding=(), stop=None):
    bars = {START - 31 * 24 * H + i * H: (price, price, price, price)
            for i in range(31 * 24 + hours) if stop is None or START - 31 * 24 * H + i * H < stop}
    return CoinTape(symbol, bars, dict(bars), dict(bars), list(funding))


def test_select_uses_only_past_funding_and_requires_positive_mean():
    tapes = dict(A=tape("A", 10, funding=[(START - H, .001)]), B=tape("B", 10, funding=[(START - H, .002)]),
                 C=tape("C", 10, funding=[(START - H, -.001)]), D=tape("D", 10, funding=[(START + H, .01)]))
    assert select(tapes, ["A", "B", "C", "D"], START, 3) == ["B", "A"]


def test_equal_slots_earn_funding_and_unfilled_slot_stays_cash():
    funding = [(START - H, .001), (START + 8 * H, .001)]
    tapes = dict(A=tape("A", 24, funding=funding), B=tape("B", 24, funding=funding))
    result = run_multi_carry(tapes, {"2024-02": ["A", "B"]}, CarryConfig(0, 0, 0, 0), 4, START, START + 24 * H)
    assert result["selections"][0]["chosen"] == ["A", "B"]
    assert result["final_equity"] == pytest.approx(10000 + 2 * 2500 * 2 / 3 * .001)


def test_missing_data_exits_position_with_doubled_slippage():
    funding = [(START - H, .001)]
    tapes = dict(ABC=tape("ABC", 24, funding=funding, stop=START + 10 * H))
    result = run_multi_carry(tapes, {"2024-02": ["ABC"]}, CarryConfig(0, 0, 0, 5), 1, START, START + 24 * H)
    assert result["data_exits"] == [dict(timestamp_ms=START + 10 * H, symbol="ABC")]
    notional = 10000 * 2 / 3
    # Entry pays 2x (non-major) spot slippage, the data exit pays 2x again.
    assert result["final_equity"] == pytest.approx(10000 - notional * 10 / 10000 - notional * 20 / 10000, rel=1e-3)


def test_registered_spot_outage_holds_position_instead_of_exiting():
    funding = [(START - H, .001)]
    base = tape("ABC", 24, funding=funding)
    gap = START + 5 * H
    spot = {t: v for t, v in base.spot.items() if t != gap}
    tapes = dict(ABC=CoinTape("ABC", base.perp, base.marks, spot, base.funding))
    held = run_multi_carry(tapes, {"2024-02": ["ABC"]}, CarryConfig(0, 0, 0, 0), 1, START, START + 24 * H, frozenset({gap}))
    assert held["data_exits"] == [] and held["final_equity"] == pytest.approx(10000)
    exited = run_multi_carry(tapes, {"2024-02": ["ABC"]}, CarryConfig(0, 0, 0, 0), 1, START, START + 24 * H)
    assert exited["data_exits"] == [dict(timestamp_ms=gap, symbol="ABC")]
