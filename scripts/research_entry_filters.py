"""Reproduce the two fixed entry-structure probes; no parameter sweep or DB saves."""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path

from app.backtest.configuration import make_strategy
from app.backtest.engine import BacktestEngine
from app.backtest.optimization import OptimizationRequestRepository
from app.backtest.results import serialize_result
from app.backtest.runs import BacktestRunRepository
from app.backtest.version_optimization import load_version_evidence
from app.data.models import Candle
from app.strategies.base import Action, Signal
from app.strategies.protection import FixedPercentageProtection


class DonchianProbe:
    """Research-only 20-day high / 10-day low breakout on completed 4h bars."""
    name = "donchian_120_60"

    def generate(self, candles: list[Candle]) -> Signal:
        if not candles:
            raise ValueError("strategy needs candle history")
        point = candles[-1]
        action = Action.HOLD
        if len(candles) >= 121:
            # The comparison window excludes the current completed candle.
            upper = max(item.high for item in candles[-121:-1])
            lower = min(item.low for item in candles[-61:-1])
            if point.close > upper:
                action = Action.BUY
            elif point.close < lower:
                action = Action.SELL
        return Signal(point.symbol, datetime.fromtimestamp(point.timestamp_ms/1000, timezone.utc),
                      action, float(action != Action.HOLD), self.name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/market.sqlite3"))
    parser.add_argument("--exchange", default="binance")
    parser.add_argument("--request-id", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = OptimizationRequestRepository(args.db).get(args.request_id)
    if request is None:
        parser.error("request does not exist")
    base = BacktestRunRepository(args.db).get_run(request.base_run_key)
    if base is None:
        parser.error("base run does not exist")
    evidence = load_version_evidence(args.db, args.exchange, base, request.evidence_run_keys)
    rows = []
    for item in evidence:
        if item.run.timeframe != "4h" or (item.run.fast_period, item.run.slow_period) != (24, 180):
            parser.error("probe is preregistered for SMA 24/180 on 4h bars")
        buffered = replace(item.config, trend_entry_buffer=0.01)
        probes = {
            "donchian_120_60": (item.config, FixedPercentageProtection(DonchianProbe(), item.config.stop_loss_pct)),
            "buffer_1pct": (buffered, make_strategy("sma", buffered, fast=24, slow=180)),
        }
        results = {}
        for name, (config, strategy) in probes.items():
            result = BacktestEngine(config).run(item.signal_candles, strategy, evaluation_start_ms=item.run.since_ms)
            results[name] = json.loads(serialize_result(result))
        rows.append(dict(source_run_key=item.run.run_key, data_fingerprint=item.run.data_fingerprint,
                         since_ms=item.run.since_ms, until_ms=item.run.until_ms,
                         source=json.loads(serialize_result(item.result)), probes=results))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dict(request_id=args.request_id, used_for_tuning=True,
                                          design="Two fixed hypotheses; no parameter sweep or independent validation",
                                          comparisons=rows), allow_nan=False), encoding="utf-8")
    print(f"Saved {len(rows)} research comparisons")


if __name__ == "__main__":
    main()
