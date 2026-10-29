"""Rerun the research baseline at the officially documented taker fee.

Binance "Futures Fee Structure & Fee Calculations" (updated 2026-05-01, accessed
2026-10-29): regular-user USD-M maker 0.02%, taker 0.05%; fee = notional x rate.
Entries/exits fill at the next open as market orders, so taker applies. This is
a new cost experiment on the same version; the 10/20 bps cases stay as stress.
"""
from dataclasses import asdict, replace
import json
from pathlib import Path

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from scripts.research_perpetual_directions import fingerprint

HOUR = 3600000
VERIFIED_TAKER_BPS = 5
BASELINE = Path("data/perpetual-swing-failure-exit.json")
OUTPUT = Path("data/verified-fee-baseline.json")


def main() -> None:
    root = Path("data/btc-perpetual-1h")
    tape = [Candle("binance-usdm", "BTC/USDT", "1h", int(r["open_time"]), *[float(r[k]) for k in ("open", "high", "low", "close", "volume")])
            for r in json.loads((root / "klines.json").read_text())]
    marks = [MarkPriceCandle("binance-usdm", "BTC/USDT", int(r["open_time"]), *[float(r[k]) for k in ("open", "high", "low", "close")], timeframe="1h")
             for r in json.loads((root / "markPriceKlines.json").read_text())]
    funding = [FundingRate("binance-usdm", "BTC/USDT", int(r["fundingTime"]), float(r["fundingRate"]), float(r["markPrice"]))
               for r in json.loads((root / "funding-api.json").read_text())]
    rows = []
    for parent in json.loads(BASELINE.read_text(encoding="utf-8"))["rows"]:
        if parent["cost_multiplier"] != 1:
            continue
        year = parent["year"]
        start = 1704067200000 if year == 2024 else 1735689600000
        end = 1735689600000 if year == 2024 else 1767225600000
        period = [c for c in tape if start - 243 * HOUR <= c.timestamp_ms < end]
        period_marks = [m for m in marks if start <= m.timestamp_ms < end]
        rates = [f for f in funding if start <= f.timestamp_ms < end]
        prints = dict(candles=fingerprint([asdict(c) for c in period]), marks=fingerprint([asdict(m) for m in period_marks]),
                      funding=fingerprint([asdict(f) for f in rates]))
        if prints != parent["input_fingerprints"]:
            raise ValueError("baseline inputs changed")
        strategies = dict(intraday=DirectionalSweepStructureConfirmStrategy(), swing=DirectionalSwingEfficiencyStrategy())
        limits = PortfolioLimits(**parent["portfolio_limits"])
        results = {}
        for label, fee, hold in (("reproduced_10bps", None, False), ("verified_taker_5bps", VERIFIED_TAKER_BPS, False),
                                 ("signal_hold_verified_taker_5bps", VERIFIED_TAKER_BPS, True)):
            sleeves = [ResearchSleeve(s["name"], strategies[s["name"]],
                                      replace(PerpetualResearchConfig(**s["config"]), **({"fee_bps": fee} if fee else {})))
                       for s in parent["sleeves"]]
            result = PortfolioResearchEngine(sleeves, limits, directional_loss_guard=True, swing_failure_exit=True,
                                            swing_long_signal_hold=hold).run(
                period, evaluation_start_ms=start, marks=period_marks, funding=rates)
            results[label] = json.loads(serialize_result(result))
        if results["reproduced_10bps"] != parent["result"]:
            raise ValueError("baseline snapshot not reproduced")
        metrics = results["verified_taker_5bps"]["metrics"]
        rows.append(dict(year=year, fee_bps=VERIFIED_TAKER_BPS, slippage_bps=5, input_fingerprints=prints,
                         parent_metrics=parent["result"]["metrics"], metrics=metrics,
                         swing_long_signal_hold_metrics=results["signal_hold_verified_taker_5bps"]["metrics"]))
        print(year, f"10bps={parent['result']['metrics']['total_return']*100:.2f}%",
              f"5bps={metrics['total_return']*100:.2f}% dd={metrics['maximum_drawdown']*100:.2f}%",
              f"trades={metrics['number_of_trades']} fees={metrics['fees']:.1f}",
              f"hold5bps={results['signal_hold_verified_taker_5bps']['metrics']['total_return']*100:.2f}%",
              f"hold_dd={results['signal_hold_verified_taker_5bps']['metrics']['maximum_drawdown']*100:.2f}%")
    OUTPUT.write_text(json.dumps(dict(schema="verified_fee_cost_case_v1", variant="portfolio_swing_failure_exit",
        fee_source="https://www.binance.com/en/support/articles/360033544231", fee_source_updated="2026-05-01",
        accessed="2026-10-29", note="Regular-user taker; VIP tiers and BNB 10% discount not assumed.",
        used_for_tuning=True, rows=rows), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
