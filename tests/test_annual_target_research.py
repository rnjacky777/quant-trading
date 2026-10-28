from dataclasses import replace

import pytest

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.data.models import Candle, TIMEFRAMES_MS
from app.strategies.base import Action
from scripts.research_annual_target import (
    BollingerAtr, DonchianMidpoint, RecordedSignals, atr14, leverage_audit,
)


def bars(count=121):
    return [Candle("binance", "BTC/USDT", "4h", i*TIMEFRAMES_MS["4h"], 100, 101, 99, 100, 1)
            for i in range(count)]


def test_simple_atr_counts_gap_from_previous_close() -> None:
    history = bars(15)
    history[-1] = replace(history[-1], open=110, high=112, low=109, close=111)
    assert atr14(history) == pytest.approx((13*2+12)/14)
    assert atr14(history[:14]) is None


def test_donchian_cache_resets_for_revised_or_shortened_prefix() -> None:
    history = bars()
    history[-1] = replace(history[-1], open=109, high=111, low=108, close=110)
    model = DonchianMidpoint()
    signal = model.generate(history)
    assert signal.action is Action.BUY and signal.stop_loss_price == 105
    assert model.generate(history) == signal
    revised = [*history[:-1], replace(history[-1], open=100, high=101, low=99, close=100)]
    assert model.generate(revised) == DonchianMidpoint().generate(revised)
    assert model.generate(history[:100]) == DonchianMidpoint().generate(history[:100])
    assert model.generate(history) == signal
    fallen = [*history, replace(history[-1], timestamp_ms=121*TIMEFRAMES_MS["4h"], open=104, high=105, low=103, close=104)]
    assert model.generate(fallen).action is Action.SELL


def test_bollinger_stop_and_per_trade_risk_audit_use_completed_signal() -> None:
    history = bars(30)
    history[19] = replace(history[19], open=91, high=92, low=89, close=90)
    history[20] = replace(history[20], open=92, high=93, low=91, close=92)
    model = BollingerAtr()
    signal = model.generate(history[:20])
    assert signal.action is Action.BUY
    assert 0 < signal.stop_loss_price < 90
    config = BacktestConfig(risk_per_trade=0.005, stop_loss_pct=0.05, exit_mode="signal")
    recorded = RecordedSignals(model)
    result = BacktestEngine(config).run(history, recorded, evaluation_start_ms=history[20].timestamp_ms)
    assert result.trades and result.trades[0].entry_timestamp_ms == history[20].timestamp_ms
    audit = leverage_audit(result, config, recorded)
    assert audit[0]["initial_stop"] == signal.stop_loss_price
    assert audit[0]["planned_risk"] <= audit[0]["risk_budget"] + 1e-8
    assert audit[0]["simulated_leverage"] == 1
    assert audit[0]["reason"]
