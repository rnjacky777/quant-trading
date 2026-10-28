"""Fixed BTC long-only position-risk scenarios using actual perpetual inputs.

Margin rates are explicit stress assumptions, NOT historical exchange brackets.
No account access, orders, version saves or signal parameter optimization.
"""
import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
from math import ceil
from pathlib import Path

from app.backtest.engine import BacktestEngine
from app.backtest.reproduction import config_for_run, strategy_for_run
from app.backtest.results import serialize_result
from app.backtest.runs import BacktestRunRepository, _fingerprint
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.risk.margin import MaintenanceMarginModel, MarginBracket


def risk_sizing(risk: float, stop: float, fee_bps: float, slippage_bps: float) -> dict:
    """Derive notional and minimum integer leverage; never infer an alpha score."""
    fee, slip = fee_bps/10000, slippage_bps/10000
    stop_fill_ratio = (1-stop)*(1-slip)
    price_and_fee_risk = 1-stop_fill_ratio + fee*(1+stop_fill_ratio)
    funding_reserve = 0.001  # One fixed 10bp notional reserve, not a prediction.
    exposure = risk/(price_and_fee_risk+funding_reserve)
    leverage = max(1, ceil(exposure))
    margin_fraction = exposure*(1+leverage*fee)/leverage
    if leverage > 2 or not 0 < margin_fraction <= 1:
        raise ValueError("scenario exceeds preregistered leverage/collateral limits")
    return dict(risk_fraction=risk, initial_stop_fraction=stop, fee_bps=fee_bps,
                slippage_bps=slippage_bps, funding_reserve_fraction=funding_reserve,
                price_and_fee_risk_fraction=price_and_fee_risk,
                target_effective_exposure=exposure, exchange_leverage=leverage,
                position_fraction=margin_fraction)


def trade_audit(result, sizing: dict) -> list[dict]:
    equity, rows = result.initial_cash, []
    for trade in result.trades:
        notional = trade.quantity*trade.entry_price
        planned = notional*(sizing["price_and_fee_risk_fraction"]+sizing["funding_reserve_fraction"])
        if abs(notional/equity-sizing["target_effective_exposure"]) > 1e-8:
            raise ValueError("actual position does not match the risk-sizing rule")
        rows.append(dict(entry_timestamp_ms=trade.entry_timestamp_ms, equity_before_entry=equity,
            risk_fraction=sizing["risk_fraction"], planned_risk_with_reserve=planned,
            notional=notional, effective_exposure=notional/equity, leverage=trade.leverage,
            actual_funding=trade.funding, pnl=trade.pnl,
            reason=f"Budget {sizing['risk_fraction']:.1%} of equity; 5% initial stop plus fees, slippage and 10bp funding reserve imply {sizing['target_effective_exposure']:.3f}x notional/equity. Minimum integer leverage {sizing['exchange_leverage']}x fits the position. This is a risk scenario, not a forecast or recommendation."))
        equity += trade.pnl
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/market.sqlite3"))
    parser.add_argument("--cache", type=Path, default=Path("data/btc-perpetual-research"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads((args.cache/"klines.json").read_text())
    tape = [Candle("binance-usdm", "BTC/USDT", "4h", int(r["open_time"]),
                   *[float(r[k]) for k in ("open","high","low","close","volume")]) for r in raw]
    raw_marks = json.loads((args.cache/"markPriceKlines.json").read_text())
    marks = [MarkPriceCandle("binance-usdm", "BTC/USDT", int(r["open_time"]),
                             *[float(r[k]) for k in ("open","high","low","close")], timeframe="4h") for r in raw_marks]
    raw_funding = json.loads((args.cache/"funding-api.json").read_text())
    funding = [FundingRate("binance-usdm", "BTC/USDT", int(r["fundingTime"]),
                           float(r["fundingRate"]), float(r["markPrice"])) for r in raw_funding]
    repository = BacktestRunRepository(args.db)
    refs = {}
    for number in (9,10,12):
        version = next(v for v in repository.list_strategy_versions() if v.strategy_family=="sma"
            and v.symbol=="BTC/USDT" and v.timeframe=="4h" and v.version_number==number)
        refs[number] = repository.list_runs_for_strategy(version.strategy_key,limit=None)[0]
    rows=[]
    for year in (2024,2025):
        start=int(datetime(year,1,1,tzinfo=timezone.utc).timestamp()*1000)
        end=int(datetime(year+1,1,1,tzinfo=timezone.utc).timestamp()*1000)
        history=[c for c in tape if start-180*14400000<=c.timestamp_ms<end]
        mark_period=[m for m in marks if start<=m.timestamp_ms<end]
        rates=[f for f in funding if start<=f.timestamp_ms<end]
        if [c.timestamp_ms for c in history]!=list(range(start-180*14400000,end,14400000)):
            raise ValueError("incomplete futures tape")
        if [m.timestamp_ms for m in mark_period]!=list(range(start,end,14400000)):
            raise ValueError("incomplete marks")
        for number, run in refs.items():
            for risk in (.005,.02,.05,.10):
                for costs in (1,2):
                    base=config_for_run(run)
                    sizing=risk_sizing(risk,base.stop_loss_pct,base.fee_bps*costs,base.slippage_bps*costs)
                    config=replace(base,risk_per_trade=None,market_type="perpetual",
                        leverage=sizing["exchange_leverage"],position_fraction=sizing["position_fraction"],
                        fee_bps=base.fee_bps*costs,slippage_bps=base.slippage_bps*costs,
                        liquidation_fee_bps=50)
                    # 2% is a conservative flat MMR STRESS assumption, not verified history.
                    result=BacktestEngine(config).run(history,strategy_for_run(run,config),
                        evaluation_start_ms=start,funding_rates=rates,mark_prices=mark_period,
                        margin_model=MaintenanceMarginModel([MarginBracket(0,1e9,.02)]))
                    rows.append(dict(year=year,version=number,risk_fraction=risk,cost_multiplier=costs,
                        margin_assumption=.02,historical_margin_brackets_verified=False,
                        tape_fingerprint=_fingerprint(history),config=asdict(config),sizing=sizing,
                        result=json.loads(serialize_result(result)),trade_audit=trade_audit(result,sizing)))
                    print(year,"V"+str(number),"risk",risk,"cost",costs,"lev",config.leverage,
                          "return",round(result.metrics.total_return*100,3),"DD",round(result.metrics.maximum_drawdown*100,3),
                          "funding",round(result.metrics.net_funding,2),"liquidations",result.metrics.liquidation_count,flush=True)
                    args.output.parent.mkdir(parents=True,exist_ok=True)
                    args.output.write_text(json.dumps(dict(target=.15,
                        limitations=["Historical margin brackets unavailable; flat 2% MMR stress assumption.",
                                      "4h mark extremes, not intrabar tick ordering.",
                                      "Funding at bar boundaries uses the existing engine event order.",
                                      "Funding reserve is not a cap on cumulative funding.",
                                      "2024/2025 already viewed development evidence, not unseen validation.",
                                      "10% risk per trade is high risk and not a recommended default."],
                        rows=rows),allow_nan=False),encoding="utf-8")


if __name__=="__main__":
    main()
