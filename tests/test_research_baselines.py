import pytest

from app.backtest.configuration import make_strategy
from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.backtest.optimization import OptimizationRequestRepository
from app.backtest.runs import BacktestRunRepository
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository
from scripts.research_strategy_baselines import compare_baselines


@pytest.mark.parametrize("timeframe", ["4h", "1d"])
def test_baseline_research_preserves_sources_and_queue(tmp_path, timeframe) -> None:
    path = tmp_path / "research.sqlite3"
    candles = [Candle("binance", "BTC/USDT", timeframe, i*TIMEFRAMES_MS[timeframe],
                      100+i, 102+i, 99+i, 101+i, 1) for i in range(60)]
    CandleRepository(path).upsert(candles)
    config = BacktestConfig(stop_loss_pct=0.05, take_profit_pct=0.15, risk_per_trade=0.005)
    result = BacktestEngine(config).run(candles, make_strategy("sma", config, fast=2, slow=3))
    runs = BacktestRunRepository(path)
    run = runs.save(result, candles, config, "development", "", 2, 3)
    requests = OptimizationRequestRepository(path)
    request = requests.enqueue(run.run_key)
    if timeframe == "1d":
        with pytest.raises(ValueError, match="only for 4h"):
            compare_baselines(path, "binance", request.request_id)
    else:
        payload = compare_baselines(path, "binance", request.request_id)
        item = payload["comparisons"][0]
        assert item["data_fingerprint"] == run.data_fingerprint
        assert item["config"]["risk_per_trade"] == 0.005
        assert len(item["baselines"]) == 3
        for baseline in item["baselines"].values():
            assert baseline["initial_cash"] == result.initial_cash
            assert baseline["equity_curve"][0] == item["source"]["equity_curve"][0]
            assert baseline["equity_curve"][-1]["timestamp_ms"] == candles[-1].timestamp_ms
    assert requests.get(request.request_id).status == "pending"
    assert len(runs.list_recent()) == 1
    assert runs.get_result(run.run_key)[0] == result


def test_donchian_probe_excludes_current_bar_from_channel() -> None:
    from scripts.research_entry_filters import DonchianProbe
    from app.strategies.base import Action
    from dataclasses import replace
    bars = [Candle("binance", "BTC/USDT", "4h", i*TIMEFRAMES_MS["4h"],100,101,99,100,1) for i in range(121)]
    probe = DonchianProbe()
    assert probe.generate(bars[:120]).action is Action.HOLD
    assert probe.generate([*bars[:-1], replace(bars[-1], high=103, close=102)]).action is Action.BUY
    assert probe.generate([*bars[:-1], replace(bars[-1], low=97, close=98)]).action is Action.SELL
