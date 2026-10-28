from datetime import datetime, timezone

import pytest

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.data.models import Candle, FundingRate, MarkPriceCandle, TIMEFRAMES_MS
from app.risk.margin import MaintenanceMarginModel, MarginBracket
from app.strategies.base import Action, Signal


STEP = TIMEFRAMES_MS["1d"]


class AlwaysLong:
    name = "always_long"

    def generate(self, candles: list[Candle]) -> Signal:
        candle = candles[-1]
        return Signal(
            candle.symbol,
            datetime.fromtimestamp(candle.timestamp_ms / 1000, timezone.utc),
            Action.BUY,
            1.0,
            self.name,
        )


def candle(index: int, price: float) -> Candle:
    return Candle("binance", "BTC/USDT", "1d", index * STEP, price, price, price, price, 1)


def mark(index: int, open_: float, high: float, low: float, close: float) -> MarkPriceCandle:
    return MarkPriceCandle("binance", "BTC/USDT", index * STEP, open_, high, low, close)


def margin_model() -> MaintenanceMarginModel:
    return MaintenanceMarginModel([MarginBracket(0, 1_000_000, 0.005, 0)])


def test_positive_funding_is_paid_by_long_and_recorded() -> None:
    result = BacktestEngine(BacktestConfig(
        fee_bps=0,
        slippage_bps=0,
        leverage=2,
        market_type="perpetual",
    )).run(
        [candle(0, 100), candle(1, 100), candle(2, 110)],
        AlwaysLong(),
        funding_rates=[FundingRate("binance", "BTC/USDT", STEP, 0.001, 100)],
        mark_prices=[mark(1, 100, 100, 100, 100), mark(2, 110, 110, 110, 110)],
        margin_model=margin_model(),
    )
    assert result.trades[0].funding == pytest.approx(-20)
    assert result.metrics.net_funding == pytest.approx(-20)
    assert result.final_equity == pytest.approx(11_980)


def test_mark_price_liquidates_before_account_equity_reaches_zero() -> None:
    result = BacktestEngine(BacktestConfig(
        fee_bps=0,
        slippage_bps=0,
        leverage=10,
        liquidation_fee_bps=50,
        market_type="perpetual",
    )).run(
        [candle(0, 100), candle(1, 100)],
        AlwaysLong(),
        funding_rates=[],
        mark_prices=[mark(1, 100, 100, 89, 89)],
        margin_model=margin_model(),
    )
    trade = result.trades[0]
    assert trade.exit_reason == "liquidation"
    assert trade.exit_price == pytest.approx(90.4522613065)
    assert trade.liquidation_fee > 0
    assert result.metrics.liquidation_count == 1
    assert result.metrics.maximum_margin_ratio >= 1


def test_perpetual_mode_refuses_incomplete_exchange_data() -> None:
    engine = BacktestEngine(BacktestConfig(market_type="perpetual"))
    with pytest.raises(ValueError, match="requires funding rates"):
        engine.run([candle(0, 100), candle(1, 100)], AlwaysLong())


def test_margin_brackets_apply_cumulative_maintenance_amount() -> None:
    model = MaintenanceMarginModel([
        MarginBracket(0, 10_000, 0.005, 0),
        MarginBracket(10_000, 50_000, 0.01, 50),
    ])
    assert model.maintenance_margin(200, 100) == pytest.approx(150)


def test_perpetual_trailing_requires_derivative_inputs_and_uses_next_bar_stop() -> None:
    config = BacktestConfig(fee_bps=0,slippage_bps=0,leverage=2,market_type="perpetual",
                            stop_loss_pct=0.05,trailing_activation=0.05,trailing_distance=0.05)
    bars = [candle(0,100),Candle("binance","BTC/USDT","1d",STEP,100,111,99,110,1),
            Candle("binance","BTC/USDT","1d",2*STEP,110,111,103,105,1)]
    with pytest.raises(ValueError,match="requires funding"):
        BacktestEngine(config).run(bars,AlwaysLong())
    result = BacktestEngine(config).run(bars,AlwaysLong(),funding_rates=[],
        mark_prices=[mark(1,100,111,99,110),mark(2,110,111,103,105)],margin_model=margin_model())
    assert result.trades[0].exit_reason=="trailing_stop"
    assert result.trades[0].exit_timestamp_ms==2*STEP
    assert result.trades[0].exit_price==pytest.approx(104.5)
    assert result.final_equity==pytest.approx(10900)
