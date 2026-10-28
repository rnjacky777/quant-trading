import pytest

from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.backtest.runs import BacktestRunRepository
from app.data.models import Candle, TIMEFRAMES_MS
from app.strategies.base import Action
from app.strategies.mean_reversion import MeanReversionStrategy
from app.strategies.momentum import MomentumStrategy


def history(prices: list[float]) -> list[Candle]:
    return [
        Candle("test", "BTC/USDT", "1d", i * TIMEFRAMES_MS["1d"], p, p, p, p, 1)
        for i, p in enumerate(prices)
    ]


def test_momentum_uses_lookback_returns_and_exits_at_threshold() -> None:
    strategy = MomentumStrategy(lookback=2, threshold=0.05)
    assert strategy.generate(history([100, 110])).action is Action.HOLD
    signal = strategy.generate(history([100, 90, 110]))
    assert signal.action is Action.BUY
    assert signal.strength == pytest.approx(0.1)
    assert signal.timestamp.utcoffset().total_seconds() == 0
    assert strategy.generate(history([100, 90, 100])).action is Action.SELL
    assert strategy.generate(history([100, 110, 90])).action is Action.SELL


def test_mean_reversion_entry_hold_and_exit() -> None:
    strategy = MeanReversionStrategy(lookback=2, entry_deviation=0.05)
    assert strategy.generate(history([100])).action is Action.HOLD
    assert strategy.generate(history([100, 80])).action is Action.BUY
    assert strategy.generate(history([100, 95])).action is Action.HOLD
    assert strategy.generate(history([100, 100])).action is Action.SELL
    assert strategy.generate(history([100, 110])).action is Action.SELL


@pytest.mark.parametrize("strategy", [MomentumStrategy(2), MeanReversionStrategy(2)])
def test_baselines_require_history_and_bound_strength(strategy) -> None:
    with pytest.raises(ValueError, match="history"):
        strategy.generate([])
    assert 0 <= strategy.generate(history([1, 1, 1000])).strength <= 1


@pytest.mark.parametrize("lookback", [0, -1, 1.5, True])
def test_invalid_lookback(lookback) -> None:
    with pytest.raises(ValueError):
        MomentumStrategy(lookback)
    with pytest.raises(ValueError):
        MeanReversionStrategy(lookback)


@pytest.mark.parametrize("value", [-0.1, 1, float("nan"), float("inf")])
def test_invalid_thresholds(value: float) -> None:
    with pytest.raises(ValueError):
        MomentumStrategy(threshold=value)
    with pytest.raises(ValueError):
        MeanReversionStrategy(entry_deviation=value)


@pytest.mark.parametrize("strategy,prices", [
    (MomentumStrategy(1), [100, 110, 200, 220]),
    (MeanReversionStrategy(2), [100, 80, 100, 120]),
])
def test_baselines_execute_after_signal_with_warmup(strategy, prices) -> None:
    candles = history(prices)
    result = BacktestEngine(BacktestConfig(fee_bps=0, slippage_bps=0)).run(
        candles, strategy, evaluation_start_ms=candles[2].timestamp_ms,
    )
    assert result.trades[0].entry_timestamp_ms == candles[2].timestamp_ms
    assert result.trades[0].entry_price == prices[2]
    assert result.final_equity == pytest.approx(10_000 * prices[3] / prices[2])


def test_strategy_version_survives_sqlite_numeric_round_trip(tmp_path) -> None:
    from app.strategies.trend_following import MovingAverageTrendStrategy

    candles = history([100, 110, 120, 130])
    config = BacktestConfig(leverage=1)
    result = BacktestEngine(config).run(candles, MovingAverageTrendStrategy(1, 2))
    repository = BacktestRunRepository(tmp_path / "runs.sqlite3")
    saved = repository.save_with_status(result, candles, config, "development", "", 1, 2)
    assert saved.strategy_created
    for _ in range(2):
        versions = repository.list_strategy_versions()
        assert len(versions) == 1
        assert versions[0].strategy_key == saved.run.strategy_key
        assert len(repository.list_runs_for_strategy(versions[0].strategy_key)) == 1


@pytest.mark.parametrize("closes,expected", [([100,100,100,100.5], Action.HOLD), ([100,100,100,110], Action.BUY), ([100,100,100,90], Action.SELL)])
def test_sma_entry_buffer_requires_strength_without_redefining_exit(closes, expected) -> None:
    from app.strategies.trend_following import MovingAverageTrendStrategy
    from app.data.models import Candle, TIMEFRAMES_MS
    bars = [Candle("test", "BTC/USDT", "4h", i*TIMEFRAMES_MS["4h"], close, close, close, close, 1) for i,close in enumerate(closes)]
    assert MovingAverageTrendStrategy(2,4,0.01).generate(bars).action is expected
    if expected is Action.HOLD:
        assert MovingAverageTrendStrategy(2,4).generate(bars).action is Action.BUY
    for bad in (-0.1, 1, float("nan")):
        with pytest.raises(ValueError):
            MovingAverageTrendStrategy(2,4,bad)
