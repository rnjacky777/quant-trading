"""Full-year descriptive analysis; no strategy changes or threshold search."""
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import sqrt, log
from pathlib import Path
from statistics import mean, median, stdev

from app.backtest.path_diagnostics import monthly_equity
from app.backtest.signal_diagnostics import HORIZONS, horizon_outcome, summarize_signals
from app.data.aggregation import completed_four_hour_bars
from app.data.models import Candle, FundingRate
from app.strategies.swing_efficiency import path_efficiency


def month(stamp: int) -> str:
    return datetime.fromtimestamp(stamp/1000, timezone.utc).strftime('%Y-%m')


def payoff(trades: list[dict]) -> dict:
    net=sum(t['pnl'] for t in trades)
    fees=sum(t['fees'] for t in trades)
    slip=sum(t['slippage_cost'] for t in trades)
    funding=sum(t['funding'] for t in trades)
    wins=sorted((t['pnl'] for t in trades if t['pnl']>0),reverse=True)
    return dict(count=len(trades),net_pnl=net,fees=fees,slippage=slip,funding=funding,
        executed_price_pnl=net+fees-funding,reference_price_pnl=net+fees+slip-funding,
        top3_winner_pnl=sum(wins[:3]),pnl_excluding_top3_winners=net-sum(wins[:3]),
        median_holding_hours=median((t['exit_timestamp_ms']-t['entry_timestamp_ms'])/3600000 for t in trades) if trades else None,
        win_rate=sum(t['pnl']>0 for t in trades)/len(trades) if trades else None)


def main() -> None:
    root=Path('data/btc-perpetual-1h')
    tape=[Candle('binance-usdm','BTC/USDT','1h',int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads((root/'klines.json').read_text())]
    funding=[FundingRate('binance-usdm','BTC/USDT',int(r['fundingTime']),float(r['fundingRate']),float(r['markPrice']))
        for r in json.loads((root/'funding-api.json').read_text())]
    times=[c.timestamp_ms for c in tape]
    source=Path('data/perpetual-swing-failure-exit.json')
    replay_path=Path('data/swing-failure-baseline-review.json')
    replay=json.loads(replay_path.read_text())
    for name,digest in replay['sources'].items():
        if sha256(Path(name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Replay source changed: {name}')
    rows=json.loads(source.read_text())['rows']
    assert len(rows)==4 and len(replay['cases'])==4 and all(c['full_snapshot_equal'] for c in replay['cases'])
    contexts={}
    def context(stamp: int) -> dict:
        if stamp not in contexts:
            i=bisect_left(times,stamp)
            bars=completed_four_hour_bars(tape[max(0,i-300):i])
            er=path_efficiency([b.close for b in bars[-21:]])
            fast=mean(b.close for b in bars[-20:]);slow=mean(b.close for b in bars[-60:])
            contexts[stamp]=dict(er20=er,regime='directional' if er>=.3 else 'low_efficiency',
                trend=1 if fast>slow else -1 if fast<slow else 0)
        return contexts[stamp]
    market=[];cases=[]
    for year,start,end in ((2024,1704067200000,1735689600000),(2025,1735689600000,1767225600000)):
        bars=[c for c in tape if start<=c.timestamp_ms<end]
        assert [c.timestamp_ms for c in bars]==list(range(start,end,3600000))
        days=defaultdict(list)
        for c in bars:days[c.timestamp_ms//86400000].append(c)
        daily_returns=[log(v[-1].close/v[0].open) for v in days.values()]
        peak=bars[0].open;dd=0.
        for c in bars:
            peak=max(peak,c.close);dd=min(dd,c.close/peak-1)
        monthly=[]
        for m in sorted({month(c.timestamp_ms) for c in bars}):
            bs=[c for c in bars if month(c.timestamp_ms)==m]
            monthly.append(dict(month=m,price_return=bs[-1].close/bs[0].open-1,
                median_hour_range_fraction=median((c.high-c.low)/c.open for c in bs)))
        regimes=Counter(context(c.timestamp_ms)['regime'] for c in bars)
        market.append(dict(year=year,hours=len(bars),days=len(days),price_return=bars[-1].close/bars[0].open-1,
            close_based_max_drawdown=dd,daily_realized_volatility=stdev(daily_returns)*sqrt(365),
            low_efficiency_hour_fraction=regimes['low_efficiency']/len(bars),monthly=monthly))
    for row in rows:
        year=row['year'];cost=row['cost_multiplier'];result=row['result'];trades=result['trades']
        audit=next(c for c in replay['cases'] if (c['year'],c['cost'])==(year,cost))
        assert audit['metrics']==result['metrics']
        groups=defaultdict(list)
        enriched=[]
        for t in trades:
            ctx=context(t['entry_timestamp_ms'])
            labels=[f"{t['sleeve']}/{t['direction']}",f"exit/{t['sleeve']}/{t['exit_reason']}",
                f"context/{t['sleeve']}/{t['direction']}/{ctx['regime']}"]
            for label in labels:groups[label].append(t)
            enriched.append(dict(t,entry_context=ctx))
        events=[]
        end=1735689600000 if year==2024 else 1767225600000
        for original in audit['signals']:
            e=dict(original);i=bisect_left(times,e['timestamp_ms']);e['entry_context']=context(e['timestamp_ms'])
            e['horizons']={}
            for h in HORIZONS:
                target=e['timestamp_ms']+h*3600000
                j=bisect_left(times,target)
                exit_bar=tape[j] if target<end and j<len(tape) and times[j]==target else None
                e['horizons'][str(h)]=horizon_outcome(tape[i],exit_bar,e['direction'],
                    fee_bps=row['config']['fee_bps'],slippage_bps=row['config']['slippage_bps'],funding=funding)
            events.append(e)
        case=dict(year=year,cost=cost,metrics=result['metrics'],frequency=audit['frequency'],
            payoff=payoff(trades),groups={k:payoff(v) for k,v in groups.items()},
            monthly_equity=monthly_equity(result,year),trades=enriched,
            signal_outcomes=dict(Counter(e['outcome']['status'] for e in events)),
            signal_summaries=summarize_signals(events),signals=events)
        cases.append(case)
        print(year,cost,json.dumps(case['payoff']),flush=True)
    paths=[source,replay_path,root/'klines.json',root/'funding-api.json',Path(__file__)]
    Path('data/full-year-strategy-review.json').write_text(json.dumps(dict(
        baseline='portfolio_swing_failure_exit',status='completed_diagnostic_only',new_candidates=0,
        used_for_tuning=True,independent_validation=False,market=market,cases=cases,
        limitations='Reference-price PnL is a fixed-trade accounting decomposition, not a zero-cost rerun. Removing top winners is sensitivity, not an executable strategy. Fixed-horizon events ignore stops and shared capital; overlapping observations are not independent. Regime uses completed past 4h only; 0.3 is inherited, not searched.',
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in paths}),ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
