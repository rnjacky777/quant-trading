"""Primary-research-inspired, single-entry-category changes from both-side R1."""
from dataclasses import asdict
import json
from pathlib import Path

from app.backtest.long_short_research import LongShortResearchEngine, PerpetualResearchConfig
from app.backtest.results import serialize_result
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.strategies.directional_intraday import DirectionalIntradayStrategy
from app.strategies.research_entry_filters import ResearchEntryFilter
from scripts.research_perpetual_directions import fingerprint


def main() -> None:
    root=Path("data/btc-perpetual-1h")
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r["open_time"]),
        *[float(r[k]) for k in ("open","high","low","close","volume")]) for r in json.loads((root/"klines.json").read_text())]
    marks=[MarkPriceCandle("binance-usdm","BTC/USDT",int(r["open_time"]),
        *[float(r[k]) for k in ("open","high","low","close")],timeframe="1h") for r in json.loads((root/"markPriceKlines.json").read_text())]
    funding=[FundingRate("binance-usdm","BTC/USDT",int(r["fundingTime"]),float(r["fundingRate"]),float(r["markPrice"]))
        for r in json.loads((root/"funding-api.json").read_text())]
    parents=json.loads(Path("data/perpetual-direction-research.json").read_text())["rows"]
    rows=[]
    for year,start,end in ((2024,1704067200000,1735689600000),(2025,1735689600000,1767225600000)):
        period=[c for c in tape if start-243*3600000<=c.timestamp_ms<end]
        period_marks=[m for m in marks if start<=m.timestamp_ms<end]
        rates=[f for f in funding if start<=f.timestamp_ms<end]
        fingerprints=dict(candles=fingerprint([asdict(c) for c in period]),marks=fingerprint([asdict(m) for m in period_marks]),
                          funding=fingerprint([asdict(f) for f in rates]))
        for costs in (1,2):
            parent=next(r for r in parents if r['year']==year and r['mode']=='both' and r['cost_multiplier']==costs)
            config=PerpetualResearchConfig(mode="both",fee_bps=10*costs,slippage_bps=5*costs)
            if parent['status']!='completed' or parent['input_fingerprints']!=fingerprints or parent['config']!=asdict(config):
                raise ValueError("exact parent experiment inputs unavailable")
            baseline=LongShortResearchEngine(config).run(period,DirectionalIntradayStrategy(),evaluation_start_ms=start,marks=period_marks,funding=rates)
            if json.loads(serialize_result(baseline))!=parent['result']:
                raise ValueError("parent evidence cannot be reproduced exactly")
            for variant in ("asia_session","volume_confirmation"):
                strategy=ResearchEntryFilter(DirectionalIntradayStrategy(),variant)
                try:
                    result=LongShortResearchEngine(config).run(period,strategy,evaluation_start_ms=start,marks=period_marks,funding=rates)
                    row=dict(year=year,variant=variant,cost_multiplier=costs,config=asdict(config),input_fingerprints=fingerprints,
                        status="completed",parent_metrics=parent['result']['metrics'],result=json.loads(serialize_result(result)))
                    print(year,variant,costs,round(result.metrics.total_return*100,3),round(result.metrics.maximum_drawdown*100,3),result.metrics.number_of_trades,flush=True)
                except (ValueError,ArithmeticError) as exc:
                    row=dict(year=year,variant=variant,cost_multiplier=costs,config=asdict(config),input_fingerprints=fingerprints,
                        status="failed",error=str(exc))
                    print(year,variant,costs,"FAILED",str(exc),flush=True)
                rows.append(row)
                Path("data/perpetual-entry-filters.json").write_text(json.dumps(dict(
                    schema="perpetual_entry_ablation_v1",parent="perpetual symmetric R1, both directions",
                    hypotheses_preregistered_in="docs/research/2026-10-27-research-entry-filters-design.md",
                    historical_margin_brackets_verified=False,rows=rows),allow_nan=False),encoding="utf-8")


if __name__=="__main__":
    main()
