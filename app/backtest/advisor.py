from dataclasses import dataclass
from math import isfinite

from app.backtest.models import BacktestConfig, BacktestResult


@dataclass(frozen=True)
class ResearchAdvice:
    decision: str
    headline: str
    explanation: str
    evidence: tuple[str, ...]
    changes: dict[str, float | int]
    validation_plan: str

    @property
    def has_candidate(self) -> bool:
        return bool(self.changes)


def analyze_backtest(
    result: BacktestResult, config: BacktestConfig
) -> ResearchAdvice:
    """Produce one controlled next experiment from observable backtest evidence."""
    metrics = result.metrics
    trades = result.trades
    stop_count = sum(trade.exit_reason == "stop_loss" for trade in trades)
    stop_ratio = stop_count / len(trades) if trades else 0.0
    evidence = (
        f"交易 {metrics.number_of_trades} 筆",
        f"總報酬 {metrics.total_return * 100:+.2f}%",
        f"最大回撤 {metrics.maximum_drawdown * 100:.2f}%",
        f"Sharpe {metrics.sharpe_ratio:.2f}",
        f"Profit Factor {_format_profit_factor(metrics.profit_factor)}",
        f"止損離場 {stop_ratio * 100:.1f}%",
    )

    if metrics.number_of_trades < 20:
        return ResearchAdvice(
            decision="collect_more_data",
            headline="先增加樣本，不建立參數型 V4",
            explanation=(
                "目前交易次數不足，單次行情可能主導結果。此時調整止盈止損"
                "很容易把雜訊當成規律。"
            ),
            evidence=evidence,
            changes={},
            validation_plan="延長 Development 區間，取得至少 20–30 筆交易後重新分析。",
        )

    if config.leverage > 1 and metrics.maximum_drawdown <= -0.15:
        target = _lower_leverage(config.leverage)
        return ResearchAdvice(
            decision="reduce_risk",
            headline=f"V4 候選：槓桿由 {config.leverage:g}x 降為 {target:g}x",
            explanation="回撤已超過 15%，先降低曝險，再評估策略訊號本身。",
            evidence=evidence,
            changes={"leverage": target},
            validation_plan="只改槓桿，使用相同資料重跑；再到 Validation 比較回撤與報酬縮減幅度。",
        )

    if (
        metrics.profit_factor < 1
        and result.strategy_name.startswith("sma_")
    ):
        parts = result.strategy_name.split("_")
        fast, slow = int(parts[1]), int(parts[2])
        target_fast = max(fast + 1, round(fast * 1.2))
        target_slow = max(target_fast + 1, round(slow * 1.2))
        return ResearchAdvice(
            decision="test_signal_filter",
            headline=f"V4 候選：SMA {fast}/{slow} 改為 {target_fast}/{target_slow}",
            explanation="Profit Factor 低於 1，先測試較慢的趨勢濾網是否能減少無效進出場。",
            evidence=evidence,
            changes={"fast": target_fast, "slow": target_slow},
            validation_plan="只修改均線週期；若 Validation 的 Profit Factor 仍低於 1，停止這條調參方向。",
        )

    if stop_ratio >= 0.5 and config.stop_loss_pct is not None:
        target = round(config.stop_loss_pct * 0.8 * 100, 2)
        return ResearchAdvice(
            decision="test_loss_control",
            headline=f"V4 候選：止損由 {config.stop_loss_pct * 100:.2f}% 改為 {target:.2f}%",
            explanation="超過一半交易由止損離場，先用單一實驗測試更早控制無效交易。",
            evidence=evidence,
            changes={"stop_loss_pct": target},
            validation_plan="比較平均虧損、勝率與 Profit Factor；若勝率惡化抵銷虧損縮小，撤回此變更。",
        )

    return ResearchAdvice(
        decision="validate",
        headline="目前不建議為 Development 報酬繼續調參",
        explanation="樣本內結果沒有明確指出單一風險參數需要修正，繼續微調會提高過度擬合風險。",
        evidence=evidence,
        changes={},
        validation_plan="固定目前版本，改用 Validation 時段測試穩定性。",
    )


def _lower_leverage(leverage: float) -> float:
    levels = (1.0, 2.0, 3.0, 5.0, 10.0)
    return max(level for level in levels if level < leverage)


def _format_profit_factor(value: float) -> str:
    return f"{value:.2f}" if isfinite(value) else "∞"
