from app.backtest.advisor import analyze_backtest
from app.backtest.models import (
    BacktestConfig,
    BacktestResult,
    PerformanceMetrics,
)


def result(*, trades: int, drawdown: float, profit_factor: float, strategy: str = "sma_20_60_trend") -> BacktestResult:
    metrics = PerformanceMetrics(
        total_return=0.10,
        cagr=0.08,
        sharpe_ratio=0.5,
        sortino_ratio=0.7,
        maximum_drawdown=drawdown,
        win_rate=0.4,
        profit_factor=profit_factor,
        average_win=100,
        average_loss=-50,
        number_of_trades=trades,
        exposure=0.5,
        fees=10,
        slippage=5,
        net_funding=0,
        liquidation_fees=0,
        liquidation_count=0,
        maximum_margin_ratio=0,
    )
    return BacktestResult(strategy, "BTC/USDT", "4h", 10_000, 11_000, metrics, [], [])


def test_advisor_refuses_to_tune_a_small_sample() -> None:
    advice = analyze_backtest(result(trades=8, drawdown=-0.05, profit_factor=1.2), BacktestConfig())
    assert advice.decision == "collect_more_data"
    assert not advice.has_candidate


def test_advisor_reduces_leverage_before_signal_tuning() -> None:
    advice = analyze_backtest(
        result(trades=30, drawdown=-0.20, profit_factor=1.1),
        BacktestConfig(leverage=5),
    )
    assert advice.changes == {"leverage": 3.0}


def test_advisor_proposes_one_sma_filter_experiment() -> None:
    advice = analyze_backtest(
        result(trades=30, drawdown=-0.10, profit_factor=0.8),
        BacktestConfig(),
    )
    assert advice.changes == {"fast": 24, "slow": 72}


def test_advisor_prioritizes_risk_budget_and_freezes_validation() -> None:
    evidence = result(trades=100, drawdown=-0.6, profit_factor=0.8)
    config = BacktestConfig(stop_loss_pct=0.05)
    assert analyze_backtest(evidence, config).changes == {"risk_per_trade_pct": 0.5}
    assert not analyze_backtest(evidence, config, research_stage="validation").has_candidate
