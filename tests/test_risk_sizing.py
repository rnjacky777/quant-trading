from dataclasses import replace

import pytest

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.data.models import Candle, TIMEFRAMES_MS
from app.risk.sizing import size_long_position
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from app.strategies.protection import FixedPercentageProtection
from app.strategies.mean_reversion import MeanReversionStrategy


def bar(i: int, price: float, low: float | None = None, high: float | None = None) -> Candle:
    return Candle("test", "BTC/USDT", "1d", i * TIMEFRAMES_MS["1d"], price, high or price, low or price, price, 1)


def size(**changes: float) -> float:
    values = dict(equity=10_000, entry_price=100, stop_price=95, risk_fraction=0.005,
                  max_exposure_fraction=1, available_cash=10_000, fee_bps=0, slippage_bps=0)
    values.update(changes)
    return size_long_position(**values)


def test_stop_distance_changes_quantity_without_changing_risk_budget() -> None:
    assert size() == pytest.approx(10)
    assert size(stop_price=90) == pytest.approx(5)
    assert size(risk_fraction=0.01) == pytest.approx(20)


def test_sizing_obeys_exposure_cash_and_invalidated_entry() -> None:
    assert size(max_exposure_fraction=0.05) == pytest.approx(5)
    assert size(available_cash=200, fee_bps=10) == pytest.approx(200 / 100.1)
    assert size(stop_price=100) == 0
    assert size(equity=0) == 0
    assert size(fee_bps=10, slippage_bps=5) < size()
    with pytest.raises(ValueError):
        size(risk_fraction=float("nan"))


def test_risk_budget_includes_round_trip_costs() -> None:
    config = BacktestConfig(risk_per_trade=0.005, stop_loss_pct=0.05, fee_bps=10, slippage_bps=5)
    strategy = FixedPercentageProtection(BuyAndHoldStrategy(), 0.05)
    result = BacktestEngine(config).run([bar(0, 100), bar(1, 100, low=90)], strategy)
    trade = result.trades[0]
    assert trade.planned_risk == pytest.approx(50)
    assert trade.pnl == pytest.approx(-50)
    assert trade.exit_reason == "stop_loss"


def test_gap_loss_can_exceed_budget_but_does_not_resize_existing_stop() -> None:
    config = BacktestConfig(risk_per_trade=0.005, stop_loss_pct=0.05, fee_bps=0, slippage_bps=0)
    result = BacktestEngine(config).run(
        [bar(0, 100), bar(1, 100), bar(2, 80)], FixedPercentageProtection(BuyAndHoldStrategy(), 0.05),
    )
    assert result.trades[0].stop_loss_price == 95
    assert result.trades[0].pnl == pytest.approx(-200)


def test_risk_mode_requires_strategy_protection_and_one_times_leverage() -> None:
    config = BacktestConfig(risk_per_trade=0.005, stop_loss_pct=0.05)
    with pytest.raises(ValueError, match="strategy stop"):
        BacktestEngine(config).run([bar(0, 100), bar(1, 100)], BuyAndHoldStrategy())
    with pytest.raises(ValueError, match="unlevered"):
        replace(config, leverage=2)


def test_signal_exit_ignores_target_but_keeps_protective_stop() -> None:
    fixed = BacktestConfig(stop_loss_pct=0.05, take_profit_pct=0.1, fee_bps=0, slippage_bps=0)
    candles = [bar(0, 100), bar(1, 100, high=120), bar(2, 100, low=90)]
    fixed_result = BacktestEngine(fixed).run(candles, BuyAndHoldStrategy())
    signal_result = BacktestEngine(replace(fixed, exit_mode="signal")).run(candles, BuyAndHoldStrategy())
    assert fixed_result.trades[0].exit_reason == "take_profit"
    assert signal_result.trades[0].exit_reason == "stop_loss"
    assert signal_result.trades[0].take_profit_price is None


def test_mean_reversion_exits_next_open_after_return_to_mean() -> None:
    config = BacktestConfig(exit_mode="signal", fee_bps=0, slippage_bps=0)
    result = BacktestEngine(config).run(
        [bar(0, 100), bar(1, 80), bar(2, 100), bar(3, 110)],
        MeanReversionStrategy(2, 0.05),
    )
    assert result.trades[0].entry_timestamp_ms == 2 * TIMEFRAMES_MS["1d"]
    assert result.trades[0].exit_timestamp_ms == 3 * TIMEFRAMES_MS["1d"]
    assert result.trades[0].exit_reason == "signal"
