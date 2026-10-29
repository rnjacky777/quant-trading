"""One risk-category change: damp repeated same-direction BTC additions."""
from dataclasses import asdict, replace
import json
from pathlib import Path

from app.backtest.long_short_research import PerpetualResearchConfig, DirectionalStrategy
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.directional_intraday import DirectionalIntradayStrategy
from app.strategies.directional_swing import DirectionalSwingStrategy
from scripts.research_perpetual_directions import fingerprint


def run_experiment(*, entry_candidate: DirectionalStrategy | None = None, risk_decay: bool = True,
        variant: str = "portfolio_overlap_decay", output: Path = Path("data/perpetual-portfolio-overlap.json"),
        swing_exit_lookback: int | None = None,
        swing_entry_candidate: DirectionalStrategy | None = None,
        intraday_holding_hours: int | None = None,
        swing_price_protection: bool = False,
        intraday_exit_candidate: DirectionalStrategy | None = None,
        directional_loss_guard: bool = False,
        swing_failure_exit: bool = False,
        slope_risk_cap: bool = False,
        intraday_price_protection: bool = False,
        swing_short_risk_cap: bool = False,
        swing_hourly_failure: bool = False,
        swing_long_signal_hold: bool = False,
        parent_path: Path = Path("data/perpetual-portfolio-research.json"),
        parent_variant: str = "portfolio_combined") -> None:
    if sum((entry_candidate is not None, risk_decay, swing_exit_lookback is not None, swing_entry_candidate is not None, intraday_holding_hours is not None, swing_price_protection, intraday_exit_candidate is not None, directional_loss_guard,swing_failure_exit,slope_risk_cap,intraday_price_protection,swing_short_risk_cap,swing_hourly_failure,swing_long_signal_hold)) != 1:
        raise ValueError("change exactly one category: entry, exit or risk")
    root=Path("data/btc-perpetual-1h")
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r["open_time"]),
        *[float(r[k]) for k in ("open","high","low","close","volume")]) for r in json.loads((root/"klines.json").read_text())]
    marks=[MarkPriceCandle("binance-usdm","BTC/USDT",int(r["open_time"]),
        *[float(r[k]) for k in ("open","high","low","close")],timeframe="1h") for r in json.loads((root/"markPriceKlines.json").read_text())]
    funding=[FundingRate("binance-usdm","BTC/USDT",int(r["fundingTime"]),float(r["fundingRate"]),float(r["markPrice"]))
        for r in json.loads((root/"funding-api.json").read_text())]
    parents=[r for r in json.loads(parent_path.read_text())['rows'] if r['variant']==parent_variant]
    if len(parents)!=4:
        raise ValueError("all four parent experiments required")
    rows=[]
    for parent in parents:
        year=parent['year'];start=1704067200000 if year==2024 else 1735689600000
        end=1735689600000 if year==2024 else 1767225600000
        period=[c for c in tape if start-243*3600000<=c.timestamp_ms<end]
        period_marks=[m for m in marks if start<=m.timestamp_ms<end]
        rates=[f for f in funding if start<=f.timestamp_ms<end]
        fingerprints=dict(candles=fingerprint([asdict(c) for c in period]),marks=fingerprint([asdict(m) for m in period_marks]),funding=fingerprint([asdict(f) for f in rates]))
        if parent['status']!='completed' or fingerprints!=parent['input_fingerprints']:
            raise ValueError("parent inputs changed or failed evidence missing")
        strategies={'intraday':DirectionalIntradayStrategy(),'swing':DirectionalSwingStrategy()}
        if parent_variant in {'portfolio_pa_smc', 'portfolio_pa_smc_confirmation', 'portfolio_confirmed_efficiency', 'portfolio_directional_pullback','portfolio_sweep_structural_stop','portfolio_directional_loss_guard','portfolio_sweep_structure_confirm','portfolio_swing_failure_exit'}:
            from app.strategies.pa_smc import DirectionalSweepStrategy
            strategies['intraday'] = DirectionalSweepStrategy()
            if parent_variant == 'portfolio_pa_smc_confirmation':
                from app.strategies.swing_confirmation import DirectionalSwingConfirmationStrategy
                strategies['swing'] = DirectionalSwingConfirmationStrategy()
            elif parent_variant in {'portfolio_confirmed_efficiency','portfolio_directional_pullback','portfolio_sweep_structural_stop','portfolio_directional_loss_guard','portfolio_sweep_structure_confirm','portfolio_swing_failure_exit'}:
                from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
                strategies['swing'] = DirectionalSwingEfficiencyStrategy()
                if parent_variant == 'portfolio_directional_pullback':
                    from app.strategies.directional_pullback import DirectionalPullbackStrategy
                    strategies['intraday'] = DirectionalPullbackStrategy()
                elif parent_variant in {'portfolio_sweep_structural_stop','portfolio_directional_loss_guard','portfolio_sweep_structure_confirm','portfolio_swing_failure_exit'}:
                    from app.strategies.sweep_structural_stop import DirectionalSweepStructuralStopStrategy
                    strategies['intraday'] = DirectionalSweepStructuralStopStrategy()
                    if parent_variant in {'portfolio_sweep_structure_confirm','portfolio_swing_failure_exit'}:
                        from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
                        strategies['intraday']=DirectionalSweepStructureConfirmStrategy()
        elif parent_variant != 'portfolio_combined':
            raise ValueError("unsupported parent strategy")
        sleeves=[ResearchSleeve(s['name'],strategies[s['name']],PerpetualResearchConfig(**s['config'])) for s in parent['sleeves']]
        limits=PortfolioLimits(**parent['portfolio_limits'])
        inherited_guard=parent.get('directional_loss_guard',False)
        inherited_failure_exit=parent.get('swing_failure_exit',False)
        if swing_failure_exit and inherited_failure_exit:
            raise ValueError("swing failure exit already enabled")
        if directional_loss_guard and inherited_guard:
            raise ValueError("directional loss guard already enabled; not a new candidate")
        candidate_guard=inherited_guard or directional_loss_guard
        baseline=PortfolioResearchEngine(sleeves,limits,directional_loss_guard=inherited_guard,swing_failure_exit=inherited_failure_exit).run(period,evaluation_start_ms=start,marks=period_marks,funding=rates)
        if json.loads(serialize_result(baseline))!=parent['result']:
            raise ValueError("parent full snapshot cannot be reproduced")
        if risk_decay:
            limits=replace(limits,same_direction_risk_decay=True)
        if entry_candidate is not None:
            sleeves=[replace(s,strategy=entry_candidate) if s.name=='intraday' else s for s in sleeves]
        if swing_exit_lookback is not None:
            sleeves=[replace(s,strategy=DirectionalSwingStrategy(swing_exit_lookback)) if s.name=='swing' else s for s in sleeves]
        if swing_entry_candidate is not None:
            sleeves=[replace(s,strategy=swing_entry_candidate) if s.name=='swing' else s for s in sleeves]
        if intraday_holding_hours is not None:
            sleeves=[replace(s,config=replace(s.config,holding_hours=intraday_holding_hours)) if s.name=='intraday' else s for s in sleeves]
        if intraday_exit_candidate is not None:
            sleeves=[replace(s,strategy=intraday_exit_candidate) if s.name=='intraday' else s for s in sleeves]
        try:
            result=PortfolioResearchEngine(sleeves,limits,swing_price_protection=swing_price_protection,
                directional_loss_guard=candidate_guard,swing_failure_exit=inherited_failure_exit or swing_failure_exit,
                slope_risk_cap=slope_risk_cap,intraday_price_protection=intraday_price_protection,
                swing_short_risk_cap=swing_short_risk_cap,swing_hourly_failure=swing_hourly_failure,
                swing_long_signal_hold=swing_long_signal_hold).run(period,evaluation_start_ms=start,marks=period_marks,funding=rates)
            summary=dict(maximum_concurrent_positions=result.maximum_concurrent_positions,
                maximum_gross_exposure=max(p.gross_exposure/p.equity for p in result.portfolio_curve),
                admission_limit_drift_bars=sum(p.admission_limit_exceeded for p in result.portfolio_curve))
            row=dict(year=year,variant=variant,mode="both",cost_multiplier=parent['cost_multiplier'],
                config=asdict(next(s.config for s in sleeves if s.name=='intraday')),portfolio_limits=asdict(limits),
                sleeves=[dict(name=s.name,strategy=s.strategy.name,config=asdict(s.config)) for s in sleeves],input_fingerprints=fingerprints,
                parent_metrics=parent['result']['metrics'],status="completed",summary=summary,result=json.loads(serialize_result(result)))
            if swing_price_protection:
                row['swing_price_protection']=dict(activation_r=1.0,stop="entry_price",effective="next_hour")
            if intraday_price_protection:
                row['intraday_price_protection']=dict(activation_r=1.0,stop="entry_price",effective="next_hour")
            if inherited_failure_exit or swing_failure_exit:
                row['swing_failure_exit']=True
            if swing_hourly_failure:
                row['swing_hourly_failure']=True
            if swing_long_signal_hold:
                row['swing_long_signal_hold']=dict(hours=72,direction='long',sleeve='swing')
            if swing_short_risk_cap:
                row['swing_short_risk_cap']=True
            if slope_risk_cap:
                row['slope_risk_cap']=True
            if intraday_exit_candidate is not None:
                row['intraday_exit_rule']=intraday_exit_candidate.name
            elif 'intraday_exit_rule' in parent:
                row['intraday_exit_rule']=parent['intraday_exit_rule']
            if candidate_guard:
                row['directional_loss_guard']=True
            print(year,parent['cost_multiplier'],round(result.metrics.total_return*100,3),round(result.metrics.maximum_drawdown*100,3),
                result.metrics.number_of_trades,result.maximum_concurrent_positions,flush=True)
        except (ValueError,ArithmeticError) as exc:
            row=dict(year=year,variant=variant,mode="both",cost_multiplier=parent['cost_multiplier'],config=parent['config'],
                portfolio_limits=asdict(limits),status="failed",error=str(exc))
        rows.append(row)
        output.write_text(json.dumps(dict(
            schema="perpetual_portfolio_exit_ablation_v1" if swing_long_signal_hold or swing_hourly_failure or intraday_price_protection or swing_failure_exit or intraday_exit_candidate is not None or swing_price_protection or swing_exit_lookback is not None or intraday_holding_hours is not None else "perpetual_portfolio_entry_ablation_v1" if entry_candidate or swing_entry_candidate else "perpetual_portfolio_risk_ablation_v1",historical_margin_brackets_verified=False,
            parent=parent_variant,category="exit" if swing_long_signal_hold or swing_hourly_failure or intraday_price_protection or swing_failure_exit or intraday_exit_candidate is not None or swing_price_protection or swing_exit_lookback is not None or intraday_holding_hours is not None else "signal" if entry_candidate or swing_entry_candidate else "risk",
            rule="Swing longs ignore strategy exit signals for the first 72h; stops, breakout-failure and time exits unchanged." if swing_long_signal_hold else "Frozen swing breakout boundary checked at every completed 1h close; exit next open." if swing_hourly_failure else "Swing short risk multiplier capped at min(existing loss brake, 0.5)." if swing_short_risk_cap else "Intraday stop moves to entry after completed close reaches 1R; effective next hour." if intraday_price_protection else "Risk budget capped at min(existing loss brake, completed 4h SMA60 24h directional slope cap)." if slope_risk_cap else "Swing frozen breakout boundary invalidation on completed 4h close; next-hour exit." if swing_failure_exit else "Risk brake=min(shared sleeve loss brake,same-direction sleeve loss brake)." if directional_loss_guard else intraday_exit_candidate.name if intraday_exit_candidate is not None else "Swing stop moves to entry after a completed close reaches 1R; effective next hour." if swing_price_protection else f"Intraday maximum holding {intraday_holding_hours}h; signal exits and initial stops unchanged." if intraday_holding_hours is not None else f"Swing exit channel {swing_exit_lookback} completed 4h bars; other rules unchanged." if swing_exit_lookback is not None else swing_entry_candidate.name if swing_entry_candidate else entry_candidate.name if entry_candidate else "Multiply entry risk by1/(1+existing BTC same-direction lots).",
            rows=rows),allow_nan=False),encoding="utf-8")


def main() -> None:
    run_experiment()


if __name__=="__main__":
    main()
