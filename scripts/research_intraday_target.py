"""Fixed short-horizon baseline for the annual 10% / max 10% DD objective."""
from dataclasses import asdict, replace
from pathlib import Path
import json

from app.backtest.catalog import VersionCatalogRepository
from app.backtest.configuration import make_strategy
from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.backtest.reproduction import reproduce_run
from app.backtest.runs import BacktestRunRepository
from app.data.repository import CandleRepository


def main() -> None:
    db = Path("data/market.sqlite3")
    repository = BacktestRunRepository(db)
    rows = []
    base = BacktestConfig(stop_loss_pct=.05, risk_per_trade=.0025, max_exposure_fraction=.5,
                          exit_mode="signal", max_entries_per_day=2, max_holding_bars=24)
    for year, start, end in ((2024, 1704067200000, 1735689600000), (2025, 1735689600000, 1767225600000)):
        tape = CandleRepository(db).list_range("binance", "BTC/USDT", "1h", start-243*3600000, end)
        if [c.timestamp_ms for c in tape] != list(range(start-243*3600000, end, 3600000)):
            raise ValueError("incomplete hourly dataset")
        for costs in (1, 2):
            config = replace(base, fee_bps=10*costs, slippage_bps=5*costs)
            result = BacktestEngine(config).run(tape, make_strategy("intraday", config), evaluation_start_ms=start)
            run = repository.save(result, tape[243:], config, "development",
                "獨立短線基準：4H20/60方向、1H20根突破、ATR14兩倍初始止損、10根低點退出、最多24h、每日2次。",
                None, None, signal_candles=tape)
            VersionCatalogRepository(db).set_category(run.strategy_key, "candidate")
            if reproduce_run(db, "binance", run)[2] != result:
                raise ValueError("saved short-horizon baseline cannot be reproduced")
            rows.append(dict(year=year,cost_multiplier=costs,run_key=run.run_key,strategy_key=run.strategy_key,
                             config=asdict(config),metrics=asdict(result.metrics)))
            print(year,costs,result.metrics.total_return,result.metrics.maximum_drawdown,result.metrics.number_of_trades,flush=True)
    Path("data/intraday-10-target-baseline.json").write_text(json.dumps(rows,indent=2,allow_nan=False),encoding="utf-8")


if __name__ == "__main__":
    main()
