"""Counterfactual one-event replays, with matched accepted-event exit audits."""
from bisect import bisect_left
from collections import defaultdict
from dataclasses import asdict, replace
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
from statistics import mean

from app.backtest.frozen_entry import FrozenEntryStrategy
from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.pa_smc import DirectionalSweepStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from scripts.research_perpetual_directions import fingerprint


def main() -> None:
    source=Path("data/all-signal-diagnostics.json")
    audit_path=Path("data/all-signal-audit.json")
    parent_path=Path("data/perpetual-confirmed-efficiency.json")
    root=Path("data/btc-perpetual-1h")
    audit=json.loads(audit_path.read_text())
    for name,digest in audit['sources'].items():
        if sha256(Path(name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f"source changed since baseline replay: {name}")
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads((root/"klines.json").read_text())]
    marks=[MarkPriceCandle("binance-usdm","BTC/USDT",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close')],timeframe="1h") for r in json.loads((root/"markPriceKlines.json").read_text())]
    funding=[FundingRate("binance-usdm","BTC/USDT",int(r['fundingTime']),float(r['fundingRate']),float(r['markPrice']))
             for r in json.loads((root/"funding-api.json").read_text())]
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    source_cases=json.loads(source.read_text())['cases']
    if len(source_cases)!=4 or {(r['year'],r['cost']) for r in source_cases}!=set(parents):
        raise ValueError("four unique baseline cases required")
    cases=[];signal_cache={}
    for case in source_cases:
        year=case['year'];parent=parents[(year,case['cost'])]
        start=1704067200000 if year==2024 else 1735689600000
        end=1735689600000 if year==2024 else 1767225600000
        period=[c for c in tape if start-243*3600000<=c.timestamp_ms<end]
        times=[c.timestamp_ms for c in period]
        period_marks=[m for m in marks if start<=m.timestamp_ms<end]
        rates=[f for f in funding if start<=f.timestamp_ms<end]
        current_fingerprints=dict(candles=fingerprint([asdict(c) for c in period]),marks=fingerprint([asdict(m) for m in period_marks]),funding=fingerprint([asdict(f) for f in rates]))
        if current_fingerprints!=parent['input_fingerprints'] or current_fingerprints!=case['input_fingerprints']:
            raise ValueError("market/funding inputs differ")
        strategies=dict(intraday=DirectionalSweepStrategy(),swing=DirectionalSwingEfficiencyStrategy())
        if year not in signal_cache:
            signal_cache[year]={name:{period[i-1].timestamp_ms:strategy.generate(period[:i])
                for i in range(243,len(period))} for name,strategy in strategies.items()}
        cached=signal_cache[year]
        expected={(timestamp+3600000,name,s.direction) for name,ss in cached.items() for timestamp,s in ss.items() if s.direction}
        if expected!={(e['timestamp_ms'],e['sleeve'],e['direction']) for e in case['signals']}:
            raise ValueError("precomputed completed-data signal set differs")
        configs={s['name']:PerpetualResearchConfig(**s['config']) for s in parent['sleeves']}
        actual={(t['entry_timestamp_ms'],t['sleeve'],t['direction']):t for t in parent['result']['trades']}
        observations=[];matched=0
        for event in case['signals']:
            entry=event['timestamp_ms'];name=event['sleeve'];config=replace(configs[name],loss_brake=False)
            j=bisect_left(times,entry)
            last=min(j+config.holding_hours,len(period)-1)
            trial_end=times[last]+3600000
            # Match nominal scheduled events even if the actual timestamp is ±1s.
            trial_rates=[f for f in rates if entry<=round(f.timestamp_ms/28800000)*28800000<trial_end]
            trial_marks=[m for m in period_marks if entry<=m.timestamp_ms<trial_end]
            wrapper=FrozenEntryStrategy(entry,cached[name])
            result=PortfolioResearchEngine([ResearchSleeve(name,wrapper,config)],PortfolioLimits(**parent['portfolio_limits'])).run(
                period[:last+1],evaluation_start_ms=entry,marks=trial_marks,funding=trial_rates)
            obs=dict(timestamp_ms=entry,sleeve=name,direction=event['direction'],parent_outcome=event['outcome'])
            if len(result.trades)>1:
                raise ValueError("isolated event produced multiple entries")
            if not result.trades:
                if event['outcome']['status']=='accepted':
                    raise ValueError("accepted parent event failed isolated entry")
                obs.update(status="unfilled",admissions=result.admissions)
                observations.append(obs)
                continue
            t=result.trades[0]
            if t.leverage!=1:
                raise ValueError("unexpected diagnostic leverage")
            obs.update(status="observed",trade=asdict(t),net_per_entry_notional=t.pnl/t.entry_notional,
                net_per_planned_risk=t.pnl/t.planned_risk,year_end_closed=t.exit_reason=='end_of_data')
            key=(entry,name,event['direction'])
            if key in actual:
                p=actual[key]
                for field in ('entry_price','exit_price','stop_loss_price'):
                    if not isclose(getattr(t,field),p[field],abs_tol=1e-8):
                        raise ValueError(f"accepted event price mismatch: {field}")
                if t.exit_timestamp_ms!=p['exit_timestamp_ms'] or t.exit_reason!=p['exit_reason']:
                    raise ValueError("accepted event exit path differs")
                for field in ('pnl','fees','funding'):
                    if not isclose(getattr(t,field)/t.quantity,p[field]/p['quantity'],rel_tol=1e-9,abs_tol=1e-7):
                        raise ValueError(f"accepted per-unit result mismatch: {field}")
                matched+=1
            if name=='intraday':
                sweep=period[j-2]
                structural=sweep.low if t.direction==1 else sweep.high
                inside=t.direction*(t.stop_loss_price-structural)>0
                exit_bar=period[bisect_left(times,t.exit_timestamp_ms)]
                not_breached=exit_bar.low>structural if t.direction==1 else exit_bar.high<structural
                obs['sweep_stop_context']=dict(structural_stop=structural,atr_stop_inside_sweep=inside,
                    stop_exit_before_extreme_even_by_bar_end=t.exit_reason=='stop_loss' and inside and not_breached)
            observations.append(obs)
        if matched!=len(actual):
            raise ValueError("not every accepted parent event was matched")
        groups=defaultdict(list)
        for obs in observations:
            if obs['status']!='observed':
                continue
            for kind in ('all',obs['parent_outcome']['status']):
                groups[(obs['sleeve'],obs['direction'],kind)].append(obs)
        summaries=[]
        for (name,side,kind),values in sorted(groups.items()):
            row=dict(sleeve=name,direction=side,scope=kind,count=len(values),
                mean_net_per_notional=mean(v['net_per_entry_notional'] for v in values),
                mean_net_r=mean(v['net_per_planned_risk'] for v in values),
                win_rate=mean(v['trade']['pnl']>0 for v in values),year_end_closed=sum(v['year_end_closed'] for v in values),
                atr_stop_inside_sweep=sum(v.get('sweep_stop_context',{}).get('atr_stop_inside_sweep',False) for v in values),
                stopped_before_sweep_extreme=sum(v.get('sweep_stop_context',{}).get('stop_exit_before_extreme_even_by_bar_end',False) for v in values))
            summaries.append(row)
            if kind=='all':
                print(year,case['cost'],name,side,'N',len(values),'meanR',round(row['mean_net_r'],3),
                    'early structural stops',row['stopped_before_sweep_extreme'],flush=True)
        cases.append(dict(year=year,cost=case['cost'],summaries=summaries,observations=observations,
            accepted_event_exit_audits=matched,actual_portfolio_metrics=parent['result']['metrics']))
        Path("data/managed-signal-diagnostics.json").write_text(json.dumps(dict(
            is_executable_portfolio_return=False,used_for_tuning=True,independent_validation=False,
            warning="Each signal has its own fixed-risk account and original exits; overlapping independent-account outcomes cannot be summed into annual portfolio return.",cases=cases),allow_nan=False),encoding="utf-8")
    sources=[source,audit_path,parent_path,root/"klines.json",root/"markPriceKlines.json",root/"funding-api.json",
             Path(__file__),Path("app/backtest/frozen_entry.py"),Path("app/backtest/portfolio_research.py")]
    Path("data/managed-signal-audit.json").write_text(json.dumps(dict(status="completed_diagnostic_only",
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in sources},
        accepted_event_checks=[dict(year=c['year'],cost=c['cost'],matched=c['accepted_event_exit_audits']) for c in cases],
        new_strategy_version=None,orders_submitted=False),indent=2),encoding="utf-8")


if __name__=="__main__":
    main()
