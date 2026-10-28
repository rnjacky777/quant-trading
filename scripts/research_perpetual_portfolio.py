"""Fixed BTC multi-lot portfolio comparison, shared cash and gross risk caps."""
from dataclasses import asdict, replace
import json
from pathlib import Path

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.directional_intraday import DirectionalIntradayStrategy
from app.strategies.directional_swing import DirectionalSwingStrategy
from scripts.research_perpetual_directions import fingerprint


def main() -> None:
    root=Path("data/btc-perpetual-1h")
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r["open_time"]),
        *[float(r[k]) for k in ("open","high","low","close","volume")]) for r in json.loads((root/"klines.json").read_text())]
    marks=[MarkPriceCandle("binance-usdm","BTC/USDT",int(r["open_time"]),
        *[float(r[k]) for k in ("open","high","low","close")],timeframe="1h") for r in json.loads((root/"markPriceKlines.json").read_text())]
    funding=[FundingRate("binance-usdm","BTC/USDT",int(r["fundingTime"]),float(r["fundingRate"]),float(r["markPrice"]))
        for r in json.loads((root/"funding-api.json").read_text())]
    limits=PortfolioLimits()
    rows=[]
    for year,start,end in ((2024,1704067200000,1735689600000),(2025,1735689600000,1767225600000)):
        period=[c for c in tape if start-243*3600000<=c.timestamp_ms<end]
        period_marks=[m for m in marks if start<=m.timestamp_ms<end]
        rates=[f for f in funding if start<=f.timestamp_ms<end]
        fingerprints=dict(candles=fingerprint([asdict(c) for c in period]),marks=fingerprint([asdict(m) for m in period_marks]),funding=fingerprint([asdict(f) for f in rates]))
        for costs in (1,2):
            config=PerpetualResearchConfig(mode="both",fee_bps=10*costs,slippage_bps=5*costs)
            intraday=ResearchSleeve("intraday",DirectionalIntradayStrategy(),config)
            swing=ResearchSleeve("swing",DirectionalSwingStrategy(),replace(config,holding_hours=168))
            for variant,sleeves in (("portfolio_intraday",[intraday]),("portfolio_swing",[swing]),("portfolio_combined",[intraday,swing])):
                try:
                    result=PortfolioResearchEngine(sleeves,limits).run(period,evaluation_start_ms=start,marks=period_marks,funding=rates)
                    summary=dict(maximum_concurrent_positions=result.maximum_concurrent_positions,
                        maximum_gross_exposure=max(p.gross_exposure/p.equity for p in result.portfolio_curve),
                        admission_limit_drift_bars=sum(p.admission_limit_exceeded for p in result.portfolio_curve))
                    row=dict(year=year,variant=variant,mode="both",cost_multiplier=costs,config=asdict(config),
                        portfolio_limits=asdict(limits),sleeves=[dict(name=s.name,strategy=s.strategy.name,config=asdict(s.config)) for s in sleeves],
                        input_fingerprints=fingerprints,status="completed",summary=summary,result=json.loads(serialize_result(result)))
                    print(year,variant,costs,round(result.metrics.total_return*100,3),round(result.metrics.maximum_drawdown*100,3),
                        "trades",result.metrics.number_of_trades,"max_positions",summary['maximum_concurrent_positions'],flush=True)
                except (ValueError,ArithmeticError) as exc:
                    row=dict(year=year,variant=variant,mode="both",cost_multiplier=costs,config=asdict(config),portfolio_limits=asdict(limits),status="failed",error=str(exc))
                    print(year,variant,costs,"FAILED",str(exc),flush=True)
                rows.append(row)
                Path("data/perpetual-portfolio-research.json").write_text(json.dumps(dict(
                    schema="perpetual_portfolio_research_v1",historical_margin_brackets_verified=False,
                    assumptions=["Independent virtual lots, not exchange-side independently isolated positions.",
                        "Shared10k cash, gross not net limits, no fixed open-position count cap.",
                        "Admission caps checked using pre-entry equity. Price/funding/fee drift is recorded, not auto-rebalanced.",
                        "Flat2% MMR per virtual lot; not historical exchange same-side aggregated margin tiers.",
                        "Hourly path and funding order limitations retained; no live execution."],rows=rows),allow_nan=False),encoding="utf-8")


if __name__=="__main__":
    main()
