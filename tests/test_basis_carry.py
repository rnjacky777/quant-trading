from datetime import datetime, timezone

import pytest

from app.backtest.basis_carry import Contract, annualized_basis, run_basis_carry
from app.backtest.funding_carry import CarryConfig
from app.data.models import Candle, MarkPriceCandle

H = 3600000
START = int(datetime(2024, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)


def candle(t, p, exchange="binance-usdm"):
    return Candle(exchange, "BTC/USDT", "1h", t, p, p, p, p, 1)


def contract(code, delivery, prices):
    candles = {t: candle(t, p) for t, p in prices.items()}
    marks = {t: MarkPriceCandle("binance-usdm", "BTC/USDT", t, p, p, p, p, timeframe="1h") for t, p in prices.items()}
    return Contract(code, delivery, candles, marks)


def flat_spot(hours, price=100.0):
    return {START + i * H: candle(START + i * H, price, "binance") for i in range(hours)}


def free():
    return CarryConfig(0, 0, 0, 0)


def test_locked_basis_converges_to_profit_without_costs():
    hours = 60
    delivery = START + 100 * H
    # Future starts 1% above spot and converges linearly towards spot.
    prices = {START + i * H: 101 - i / hours for i in range(hours)}
    result = run_basis_carry(flat_spot(hours), [contract("A", delivery, prices)], free(), 0.0, START, START + hours * H)
    quantity = 10000 * 2 / 3 / 100
    assert result["final_equity"] == pytest.approx(10000 + quantity * (101 - prices[START + (hours - 1) * H]))
    assert [e["reason"] for e in result["entries"]] == ["entry"]


def test_threshold_blocks_entry_when_annualized_basis_is_too_small():
    hours = 30
    delivery = START + 1000 * H
    prices = {START + i * H: 100.1 for i in range(hours)}
    basis = annualized_basis(100.1, 100, START, delivery)
    assert basis == pytest.approx(.001 * 8760 / 1000)
    blocked = run_basis_carry(flat_spot(hours), [contract("A", delivery, prices)], free(), basis + .01, START, START + hours * H)
    assert blocked["entries"] == [] and blocked["final_equity"] == 10000 and blocked["invested_hours"] == 0
    taken = run_basis_carry(flat_spot(hours), [contract("A", delivery, prices)], free(), basis - .01, START, START + hours * H)
    assert len(taken["entries"]) == 1


def test_rolls_24h_before_delivery_into_next_contract_or_cash():
    hours = 80
    first_delivery = START + 50 * H
    a = contract("A", first_delivery, {START + i * H: 101 for i in range(27)})
    b_prices = {START + i * H: 102 for i in range(hours)}
    rolled = run_basis_carry(flat_spot(hours), [a, contract("B", START + 3000 * H, b_prices)], free(), 0.0, START, START + hours * H)
    assert [(e["contract"], e["reason"], e["timestamp_ms"]) for e in rolled["entries"]] == [
        ("A", "entry", START), ("B", "roll", first_delivery - 24 * H)]
    to_cash = run_basis_carry(flat_spot(hours), [a, contract("B", START + 3000 * H, {t: 99.0 for t in b_prices})],
                              free(), 0.0, START, START + hours * H)
    assert to_cash["rebalances"][-1]["reason"] == "roll_to_cash"
    assert len(to_cash["entries"]) == 1 and to_cash["final_equity"] == pytest.approx(10000)


def test_costs_reduce_return_and_account_reconciles():
    hours = 40
    prices = {START + i * H: 101 for i in range(hours)}
    free_run = run_basis_carry(flat_spot(hours), [contract("A", START + 500 * H, prices)], free(), 0.0, START, START + hours * H)
    costly = run_basis_carry(flat_spot(hours), [contract("A", START + 500 * H, prices)], CarryConfig(5, 5, 10, 5), 0.0,
                             START, START + hours * H)
    assert free_run["final_equity"] == pytest.approx(10000)
    assert costly["final_equity"] < 10000 and costly["fees"] > 0
