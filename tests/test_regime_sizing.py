from dataclasses import replace

import pytest

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.data.models import Candle, TIMEFRAMES_MS
from app.risk.regime import slow_slope_multiplier
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from app.strategies.protection import FixedPercentageProtection


def bars(prices):
    return [Candle("test", "BTC/USDT", "4h", i * TIMEFRAMES_MS["4h"],
                   p, p, p, p, 1) for i, p in enumerate(prices)]


def test_slope_uses_completed_history_and_reduces_flat_down_or_short_history():
    assert slow_slope_multiplier(bars(range(100, 286)), 180) == 1
    assert slow_slope_multiplier(bars(range(286, 100, -1)), 180) == .5
    assert slow_slope_multiplier(bars([100] * 186), 180) == .5
    assert slow_slope_multiplier(bars([100] * 180), 180) == .5


def test_reduced_budget_changes_quantity_not_signal_or_stop_and_ignores_entry_bar_close():
    config = BacktestConfig(stop_loss_pct=.05, risk_per_trade=.005,
                            risk_regime="slow_slope", fee_bps=0, slippage_bps=0)
    history = bars([100] * 187)
    strategy = FixedPercentageProtection(BuyAndHoldStrategy(), .05)
    result = BacktestEngine(config).run(history, strategy, evaluation_start_ms=history[186].timestamp_ms)
    fixed = BacktestEngine(replace(config, risk_regime="fixed")).run(
        history, strategy, evaluation_start_ms=history[186].timestamp_ms)
    assert result.trades[0].quantity == fixed.trades[0].quantity / 2
    assert result.trades[0].stop_loss_price == fixed.trades[0].stop_loss_price
    assert result.trades[0].planned_risk == pytest.approx(25)
    history[-1] = replace(history[-1], high=200, close=200)
    changed = BacktestEngine(config).run(history, strategy, evaluation_start_ms=history[186].timestamp_ms)
    assert changed.trades[0].quantity == result.trades[0].quantity


def test_regime_rejects_missing_risk_budget():
    with pytest.raises(ValueError, match="risk budget"):
        BacktestConfig(risk_regime="slow_slope")
