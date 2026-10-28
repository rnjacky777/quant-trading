from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from app.backtest.models import BacktestResult
from app.backtest.reproduction import reproduce_run
from app.backtest.runs import BacktestRun, BacktestRunRepository


@dataclass(frozen=True)
class ComparisonEntry:
    run: BacktestRun
    version: int | None
    result: BacktestResult | None
    source: str
    error: str = ""


def load_comparison(path: Path, exchange: str, keys: list[str]) -> list[ComparisonEntry]:
    if len(keys) != 2 or len(set(keys)) != 2:
        raise ValueError("請選擇兩筆不同的回測紀錄")
    repository = BacktestRunRepository(path)
    runs = [repository.get_run(key) for key in keys]
    if any(run is None for run in runs):
        raise ValueError("選擇的回測紀錄不存在，請重新選擇")
    return [_load_entry(repository, path, exchange, run) for run in runs]


def load_saved_result(path: Path, exchange: str, run_key: str) -> ComparisonEntry:
    repository = BacktestRunRepository(path)
    run = repository.get_run(run_key)
    if run is None:
        raise ValueError("回測紀錄不存在")
    return _load_entry(repository, path, exchange, run)


def _load_entry(repository: BacktestRunRepository, path: Path, exchange: str, run: BacktestRun) -> ComparisonEntry:
    snapshot = repository.get_result(run.run_key)
    error = ""
    if snapshot is None:
        try:
            result = reproduce_run(path, exchange, run)[2]
            repository.save_reproduced_result(run.run_key, result)
            snapshot = repository.get_result(run.run_key)
        except (ValueError, RuntimeError) as exc:
            error = f"舊紀錄無法精確重現：{exc}"
    version = repository.get_strategy_version_for_run(run.run_key)
    return ComparisonEntry(run, version.version_number if version else None,
                           snapshot[0] if snapshot else None,
                           snapshot[1] if snapshot else "unavailable", error)


def comparison_warnings(entries: list[ComparisonEntry]) -> list[str]:
    left, right = (entry.run for entry in entries)
    warnings = []
    for fields, label in (
        (("since_ms", "until_ms"), "回測日期不同，不能直接判定同期間的策略優劣"),
        (("symbol", "timeframe"), "交易對或 K 線週期不同"),
        (("initial_cash",), "初始資金不同，請同時參考報酬率或切換起始 100 的曲線"),
        (("fee_bps", "slippage_bps"), "手續費率或模擬滑價設定不同"),
        (("stop_loss_pct", "take_profit_pct", "leverage", "policy_json"), "止盈止損、倉位風險或出場設定不同；此處比較完整交易設定"),
    ):
        if any(getattr(left, field) != getattr(right, field) for field in fields):
            # Strategy-specific parameters in policy_json are expected to differ.
            if fields == ("stop_loss_pct", "take_profit_pct", "leverage", "policy_json"):
                policies = [json.loads(run.policy_json) for run in (left, right)]
                for policy in policies:
                    policy.pop("strategy_name", None)
                defaults = dict(risk_per_trade=None, max_exposure_fraction=1.0, exit_mode="fixed", position_fraction=1.0, stop_reentry_mode="immediate", trend_entry_buffer=0.0, trailing_activation=None, trailing_distance=None, trailing_reentry_mode="inherit")
                if all(getattr(left, name) == getattr(right, name) for name in fields[:-1]) and {**defaults, **policies[0]} == {**defaults, **policies[1]}:
                    continue
            warnings.append(label)
    if left.data_fingerprint != right.data_fingerprint:
        warnings.append("資料指紋不同，可能包含不同暖機長度或市場資料版本；不可視為完全相同輸入")
    return warnings


def comparison_chart(entries: list[ComparisonEntry], mode: str = "equity") -> dict[str, object]:
    available = [(index, entry) for index, entry in enumerate(entries) if entry.result is not None]
    if not available:
        return {"series": []}
    times = [point.timestamp_ms for _, entry in available for point in entry.result.equity_curve]
    start, end = min(times), max(times)
    series = []
    for index, entry in available:
        values = [(point.timestamp_ms, point.equity * (100 / entry.run.initial_cash if mode == "indexed" else 1))
                  for point in entry.result.equity_curve]
        series.append((index, values))
    all_values = [value for _, values in series for _, value in values]
    low, high = min(all_values), max(all_values)
    padding = max((high-low)*0.05, abs(high)*0.005, 0.01)
    low, high = low-padding, high+padding
    paths = [dict(index=index, points=" ".join(
        f"{80+(timestamp-start)/max(end-start,1)*850:.2f},{260-(value-low)/(high-low)*235:.2f}"
        for timestamp, value in values
    )) for index, values in series]
    return dict(series=paths, low=low, high=high,
                start=datetime.fromtimestamp(start/1000, timezone.utc).strftime("%Y-%m-%d"),
                end=datetime.fromtimestamp(end/1000, timezone.utc).strftime("%Y-%m-%d"))
