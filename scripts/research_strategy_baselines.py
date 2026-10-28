"""Compare fixed, unswept baselines against every marked version experiment.

Writes research artifacts only; never creates versions or processes the queue.
"""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path

from app.backtest.configuration import make_strategy
from app.backtest.engine import BacktestEngine
from app.backtest.optimization import OptimizationRequestRepository
from app.backtest.results import serialize_result
from app.backtest.runs import BacktestRunRepository
from app.backtest.version_optimization import load_version_evidence


def compare_baselines(path: Path, exchange: str, request_id: int) -> dict[str, object]:
    request = OptimizationRequestRepository(path).get(request_id)
    if request is None:
        raise ValueError("optimization request does not exist")
    base = BacktestRunRepository(path).get_run(request.base_run_key)
    if base is None:
        raise ValueError("base run does not exist")
    evidence = load_version_evidence(path, exchange, base, request.evidence_run_keys)
    comparisons = []
    for item in evidence:
        if item.run.timeframe != "4h":
            raise ValueError("weekly 42-bar baseline is defined only for 4h bars")
        # SMA-specific entry filters do not transfer to other signal families.
        config = replace(item.config, trend_entry_buffer=0.0)
        variants = {
            "weekly_momentum_42": make_strategy("momentum", config, lookback=42),
            "mean_reversion_20_5pct": make_strategy("mean-reversion", config, lookback=20, entry_deviation=0.05),
            # This repeatedly re-enters after protection exits, unlike buy-and-hold.
            "always_long_same_protection": make_strategy("buy-hold", config),
        }
        results = {}
        for name, strategy in variants.items():
            result = BacktestEngine(config).run(
                item.signal_candles, strategy, evaluation_start_ms=item.run.since_ms,
            )
            results[name] = json.loads(serialize_result(result))
        comparisons.append(dict(
            source_run_key=item.run.run_key, data_fingerprint=item.run.data_fingerprint,
            since_ms=item.run.since_ms, until_ms=item.run.until_ms,
            config=asdict(config), source_config=asdict(item.config), source_used_for_tuning=True,
            source=json.loads(serialize_result(item.result)), baselines=results,
        ))
    return dict(
        request_id=request_id, strategy_key=base.strategy_key,
        design="Fixed parameters selected before baseline results; no parameter sweep.",
        limitations=[
            "Exploratory reused evidence; overlapping results are not independent.",
            "All variants use the source's exact candles, warmup, costs and protection.",
            "Weekly momentum is an engineering baseline, not a replication of a paper.",
            "Always-long with protection is not a passive buy-and-hold benchmark.",
            "Fixed slippage does not establish liquidity capacity or real fill quality.",
        ], comparisons=comparisons,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/market.sqlite3"))
    parser.add_argument("--exchange", default="binance")
    parser.add_argument("--request-id", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = compare_baselines(args.db, args.exchange, args.request_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(f"Saved {len(payload['comparisons'])} period comparisons to {args.output}")


if __name__ == "__main__":
    main()
