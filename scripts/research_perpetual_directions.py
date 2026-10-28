"""Frozen long/short ablation with actual hourly futures data and funding."""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.long_short_research import LongShortResearchEngine, PerpetualResearchConfig
from app.backtest.results import serialize_result
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.strategies.directional_intraday import DirectionalIntradayStrategy


def fingerprint(value) -> str:
    return sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def main() -> None:
    root=Path("data/btc-perpetual-1h")
    raw=json.loads((root/"klines.json").read_text())
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r["open_time"]),
        *[float(r[k]) for k in ("open","high","low","close","volume")]) for r in raw]
    raw_marks=json.loads((root/"markPriceKlines.json").read_text())
    marks=[MarkPriceCandle("binance-usdm","BTC/USDT",int(r["open_time"]),
        *[float(r[k]) for k in ("open","high","low","close")],timeframe="1h") for r in raw_marks]
    raw_funding=json.loads((root/"funding-api.json").read_text())
    funding=[FundingRate("binance-usdm","BTC/USDT",int(r["fundingTime"]),float(r["fundingRate"]),float(r["markPrice"])) for r in raw_funding]
    rows=[]
    for year,start,end in ((2024,1704067200000,1735689600000),(2025,1735689600000,1767225600000)):
        period=[c for c in tape if start-243*3600000<=c.timestamp_ms<end]
        period_marks=[m for m in marks if start<=m.timestamp_ms<end]
        rates=[f for f in funding if start<=f.timestamp_ms<end]
        fingerprints=dict(candles=fingerprint([asdict(c) for c in period]),marks=fingerprint([asdict(m) for m in period_marks]),
                          funding=fingerprint([asdict(f) for f in rates]))
        for mode in ("long_only","short_only","both"):
            for costs in (1,2):
                config=PerpetualResearchConfig(mode=mode,fee_bps=10*costs,slippage_bps=5*costs)
                try:
                    result=LongShortResearchEngine(config).run(period,DirectionalIntradayStrategy(),
                        evaluation_start_ms=start,marks=period_marks,funding=rates)
                    row=dict(year=year,mode=mode,cost_multiplier=costs,config=asdict(config),input_fingerprints=fingerprints,
                        status="completed",result=json.loads(serialize_result(result)))
                    print(year,mode,costs,round(result.metrics.total_return*100,3),
                        round(result.metrics.maximum_drawdown*100,3),result.metrics.number_of_trades,
                        "funding",round(result.metrics.net_funding,2),"liq",result.metrics.liquidation_count,flush=True)
                except (ValueError,ArithmeticError) as exc:
                    row=dict(year=year,mode=mode,cost_multiplier=costs,config=asdict(config),input_fingerprints=fingerprints,
                        status="failed",error=str(exc))
                    print(year,mode,costs,"FAILED",str(exc),flush=True)
                rows.append(row)
                Path("data/perpetual-direction-research.json").write_text(json.dumps(dict(
                    schema="directional_perpetual_research_v1",historical_margin_brackets_verified=False,
                    assumptions=["Flat2% MMR, not actual historical brackets.",
                        "Hourly mark extremes; liquidation checked before trade stop, no tick ordering.",
                        "Funding exactly at open goes to old position; intra-hour events go to post-open position before extremes.",
                        "No intrabar partial fills, spread depth or liquidation insurance/ADL model.",
                        "Confidence score not calibrated; no confidence-based leverage increase.",
                        "2024/2025 are tuning evidence, not independent unseen validation."],
                    rows=rows),allow_nan=False),encoding="utf-8")


if __name__=="__main__":
    main()
