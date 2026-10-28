from dataclasses import dataclass, replace
from math import isclose
from pathlib import Path

from app.backtest.advisor import ResearchAdvice, analyze_backtest
from app.backtest.models import BacktestConfig, BacktestResult
from app.backtest.reproduction import reproduce_run
from app.backtest.runs import BacktestRun, BacktestRunRepository
from app.data.models import Candle


@dataclass(frozen=True)
class VersionEvidence:
    run: BacktestRun
    candles: list[Candle]
    signal_candles: list[Candle]
    result: BacktestResult
    config: BacktestConfig


def load_version_evidence(
    path: Path, exchange: str, base: BacktestRun, run_keys: list[str] | None = None,
) -> list[VersionEvidence]:
    repo = BacktestRunRepository(path)
    runs = repo.list_runs_for_strategy(base.strategy_key, limit=None)
    by_key = {run.run_key: run for run in runs}
    keys = run_keys if run_keys is not None else list(by_key)
    if not keys or base.run_key not in keys:
        raise ValueError("優化證據必須包含指定父版本的基準回測")
    evidence = []
    for key in keys:
        if key not in by_key:
            raise ValueError("優化證據缺失或屬於其他策略版本")
        run = by_key[key]
        candles, signals, result, config = reproduce_run(path, exchange, run)
        if not isclose(result.final_equity, run.final_equity, rel_tol=1e-10, abs_tol=1e-8):
            raise ValueError(f"保存的回測無法重現：{key}")
        evidence.append(VersionEvidence(run, candles, signals, result, config))
    return evidence


def analyze_version(evidence: list[VersionEvidence]) -> ResearchAdvice:
    """Inspect every period; never add returns/trades across overlapping runs.

    Priorities are fixed: lower leverage, risk sizing, signal filtering, stop
    control. Repeated datasets are not independent votes. This is deterministic
    research assistance, not an autonomous model or a profitability guarantee.
    """
    if not evidence:
        raise ValueError("策略版本尚無可分析的回測")
    unique: dict[tuple[object, ...], VersionEvidence] = {}
    for item in evidence:
        run = item.run
        unique.setdefault((run.since_ms, run.until_ms, run.data_fingerprint,
                           run.initial_cash, run.fee_bps, run.slippage_bps), item)
    advice = [analyze_backtest(item.result, item.config) for item in unique.values()]
    priorities = {"reduce_risk": 0, "test_risk_budget": 1, "test_signal_filter": 2, "test_loss_control": 3}
    candidates = [item for item in advice if item.has_candidate]
    chosen = min(candidates, key=lambda item: priorities.get(item.decision, 99)) if candidates else advice[0]
    overview = tuple(
        f"{item.run.run_key[:10]} · {item.run.stage} · 報酬 {item.result.metrics.total_return:+.2%} · 回撤 {item.result.metrics.maximum_drawdown:.2%} · {item.result.metrics.number_of_trades} 筆"
        for item in evidence
    )
    return replace(
        chosen,
        explanation=f"已檢查此版本 {len(evidence)} 筆回測（{len(unique)} 組不同實驗資料）；不把重疊期間加總或視為獨立驗證。{chosen.explanation}",
        evidence=overview,
        validation_plan="所有參考結果均已用於優化，不能再標為獨立未見驗證。候選須在每個相同區間與成本重跑比較；另用尚未參考的資料驗證。",
    )
