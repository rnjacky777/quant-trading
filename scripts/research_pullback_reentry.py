"""Preregistered V13 reentry comparison; no orders or version writes."""
from dataclasses import replace
from pathlib import Path
import json

from app.backtest.engine import BacktestEngine
from app.backtest.reproduction import config_for_run, strategy_for_run
from app.backtest.results import serialize_result
from app.backtest.runs import BacktestRunRepository, _fingerprint
from app.data.repository import CandleRepository


def main() -> None:
    db = Path("data/market.sqlite3")
    repo = BacktestRunRepository(db)
    version = next(v for v in repo.list_strategy_versions() if v.strategy_family == "sma" and v.version_number == 13)
    runs = repo.list_runs_for_strategy(version.strategy_key, limit=None)
    rows = []
    for year, start, end in ((2024, 1704067200000, 1735689600000), (2025, 1735689600000, 1767225600000)):
        run = next(r for r in runs if r.since_ms == start and r.until_ms == end - 14400000 and r.fee_bps == 10)
        tape = CandleRepository(db).list_range("binance", "BTC/USDT", "4h", start - 180 * 14400000, end)
        if len(tape) != 180 + (end-start)//14400000:
            raise ValueError("incomplete data")
        for mode in ("inherit", "pullback_reclaim"):
            for cost in (1, 2):
                base = config_for_run(run)
                config = replace(base, trailing_reentry_mode=mode, fee_bps=base.fee_bps*cost, slippage_bps=base.slippage_bps*cost)
                result = BacktestEngine(config).run(tape, strategy_for_run(run, config), evaluation_start_ms=start)
                rows.append(dict(year=year, mode=mode, cost=cost, fingerprint=_fingerprint(tape),
                                 result=json.loads(serialize_result(result))))
                print(year, mode, cost, result.metrics.total_return, result.metrics.maximum_drawdown, result.metrics.number_of_trades, flush=True)
    Path("data/pullback-reclaim-annual.json").write_text(json.dumps(rows, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
