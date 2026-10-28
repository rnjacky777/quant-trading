"""Save a fixed V12-parameter 1h baseline, not a multi-timeframe strategy."""
from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import median

from app.backtest.catalog import VersionCatalogRepository
from app.backtest.engine import BacktestEngine
from app.backtest.reproduction import config_for_run, reproduce_run, strategy_for_run
from app.backtest.runs import BacktestRunRepository, _fingerprint
from app.data.repository import CandleRepository


def main() -> None:
    db = Path("data/market.sqlite3")
    repo = BacktestRunRepository(db)
    parent = next(v for v in repo.list_strategy_versions() if v.strategy_family == "sma" and v.timeframe == "4h" and v.version_number == 12)
    source = next(r for r in repo.list_runs_for_strategy(parent.strategy_key, limit=None)
                  if r.since_ms == 1735689600000 and r.until_ms == 1767211200000 and r.fee_bps == 10)
    base = config_for_run(source)
    rows = []
    for year, start, end in ((2024, 1704067200000, 1735689600000), (2025, 1735689600000, 1767225600000)):
        tape = CandleRepository(db).list_range("binance", "BTC/USDT", "1h", start - 180*3600000, end)
        if [c.timestamp_ms for c in tape] != list(range(start-180*3600000, end, 3600000)):
            raise ValueError("incomplete hourly tape or warmup")
        period = tape[180:]
        for cost in (1, 2):
            config = replace(base, fee_bps=base.fee_bps*cost, slippage_bps=base.slippage_bps*cost)
            result = BacktestEngine(config).run(tape, strategy_for_run(source, config), evaluation_start_ms=start)
            saved = repo.save(result, period, config, "development",
                "V12相同數值參數移至1h的基準；非4h方向+1h進場策略，未實作每日次數限制。",
                source.fast_period, source.slow_period, signal_candles=tape)
            VersionCatalogRepository(db).set_category(saved.strategy_key, "candidate")
            # Saved periods and snapshots must reproduce exactly through the normal path.
            replay = reproduce_run(db, "binance", saved)[2]
            if replay != result:
                raise ValueError("saved hourly experiment cannot be reproduced")
            entries = Counter(datetime.fromtimestamp(t.entry_timestamp_ms/1000, timezone.utc).strftime("%Y-%m-%d") for t in result.trades)
            days = (end-start)//86400000
            rows.append(dict(year=year, cost_multiplier=cost, config=asdict(config), source_strategy_key=source.strategy_key,
                strategy_key=saved.strategy_key, version=repo.get_strategy_version(saved.strategy_key).version_number,
                run_key=saved.run_key, fingerprint=_fingerprint(tape), final_equity=result.final_equity,
                metrics=asdict(result.metrics), entries_per_calendar_day=len(result.trades)/days,
                active_entry_days=len(entries), maximum_entries_in_one_utc_day=max(entries.values(), default=0),
                median_holding_hours=median((t.exit_timestamp_ms-t.entry_timestamp_ms)/3600000 for t in result.trades) if result.trades else 0,
                frequency_note="Observed frequency only; no daily cap or multi-timeframe filter implemented."))
            print(year, cost, result.metrics.total_return, result.metrics.maximum_drawdown,
                  result.metrics.number_of_trades, rows[-1]["median_holding_hours"], flush=True)
    Path("data/hourly-v12-baseline.json").write_text(json.dumps(rows, indent=2, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
