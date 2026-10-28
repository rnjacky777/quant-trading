import pytest

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.data.models import Candle
from app.risk.regime import loss_streak_multiplier
from app.risk.sizing import minimum_required_leverage
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from app.strategies.protection import FixedPercentageProtection


def test_loss_streak_brake_only_uses_closed_losses_and_resets_on_profit():
    assert loss_streak_multiplier([]) == 1
    assert loss_streak_multiplier([-1]) == 1
    assert loss_streak_multiplier([-1, -1]) == .5
    assert loss_streak_multiplier([-1, -1, 0]) == .5
    assert loss_streak_multiplier([-1, -1, 1]) == 1
    assert loss_streak_multiplier([-1, 1, -1]) == 1


def test_actual_risk_budget_halves_after_second_loss_and_restarts_each_run():
    config = BacktestConfig(stop_loss_pct=.05, risk_per_trade=.0025,
                            risk_regime="loss_streak", fee_bps=0, slippage_bps=0)
    bars = [Candle("test", "BTC/USDT", "1h", i*3600000, 100, 100, 94, 100, 1) for i in range(5)]
    engine = BacktestEngine(config)
    strategy = FixedPercentageProtection(BuyAndHoldStrategy(), .05)
    result = engine.run(bars, strategy)
    equity = 10000
    for i, trade in enumerate(result.trades):
        expected = .0025 if i < 2 else .00125
        assert trade.planned_risk/equity == pytest.approx(expected)
        equity += trade.pnl
    assert engine.run(bars, strategy) == result


def test_leverage_is_minimum_collateral_requirement_not_a_confidence_multiplier():
    assert minimum_required_leverage(notional=5000, equity=10000) == 1
    assert minimum_required_leverage(notional=15000, equity=10000) == 2
    assert minimum_required_leverage(notional=0, equity=10000) == 0
    with pytest.raises(ValueError, match="limit"):
        minimum_required_leverage(notional=25000, equity=10000)
    with pytest.raises(ValueError):
        minimum_required_leverage(notional=1000, equity=0)
