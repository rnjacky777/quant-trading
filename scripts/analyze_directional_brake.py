"""Rebuild only already-closed PnL available before each structural entry."""
from bisect import bisect_left
from collections import defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.long_short_research import LongShortResearchEngine, PerpetualResearchConfig
from app.data.models import Candle
from app.risk.regime import loss_streak_multiplier
from app.strategies.sweep_structural_stop import DirectionalSweepStructuralStopStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy


def main() -> None:
    source=Path("data/perpetual-sweep-structural-stop.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape];rows=json.loads(source.read_text())['rows'];cases=[]
    if len(rows)!=4 or {(r['year'],r['cost_multiplier']) for r in rows}!={(2024,1),(2024,2),(2025,1),(2025,2)}:
        raise ValueError("four unique baseline cases required")
    for row in rows:
        if row['result']['metrics']['liquidation_count'] or row['portfolio_limits']['same_direction_risk_decay']:
            raise ValueError("diagnostic currently scoped to non-liquidating un-decayed structural baseline")
        trades=row['result']['trades'];by_id={t['position_id']:t for t in trades}
        configs={s['name']:PerpetualResearchConfig(**s['config']) for s in row['sleeves']}
        warmup=bisect_left(times,(1704067200000 if row['year']==2024 else 1735689600000)-243*3600000)
        groups=defaultdict(lambda:dict(count=0,pnl=0.,net_r_sum=0.,wins=0));events=[]
        for admission in row['result']['admissions']:
            if admission['status']!='accepted':
                continue
            i=bisect_left(times,admission['timestamp_ms']);entry=tape[i]
            # Opening exits are available; same-bar intrabar stops are not.
            available=[t for t in trades if t['exit_timestamp_ms']<entry.timestamp_ms or
                (t['exit_timestamp_ms']==entry.timestamp_ms and t['entry_timestamp_ms']<entry.timestamp_ms and (t['exit_reason'] in {'signal','time_limit'} or
                t['exit_reason']=='stop_loss' and t['direction']*(entry.open-t['stop_loss_price'])<=0))]
            closed=[t for t in available if t['sleeve']==admission['sleeve']]
            shared=loss_streak_multiplier([t['pnl'] for t in closed])
            own=loss_streak_multiplier([t['pnl'] for t in closed if t['direction']==admission['direction']])
            strategy=DirectionalSweepStructuralStopStrategy() if admission['sleeve']=='intraday' else DirectionalSwingEfficiencyStrategy()
            signal=strategy.generate(tape[warmup:i])
            _,proposal=LongShortResearchEngine(configs[admission['sleeve']])._open(admission['equity_before'],entry,signal,shared)
            if proposal is None or not isclose(proposal.planned_risk*admission['scale'],admission['planned_risk'],abs_tol=1e-7):
                raise ValueError("reconstructed shared brake does not match actual sizing")
            kind='extra_brake' if own<shared else 'would_restore' if own>shared else 'same'
            trade=by_id[admission['position_id']]
            group=groups[f"{admission['sleeve']}/{admission['direction']}/{kind}"]
            group['count']+=1;group['pnl']+=trade['pnl'];group['net_r_sum']+=trade['pnl']/trade['planned_risk'];group['wins']+=trade['pnl']>0
            events.append(dict(position_id=trade['position_id'],sleeve=admission['sleeve'],direction=admission['direction'],
                shared_multiplier=shared,directional_multiplier=own,proposed_guard=min(shared,own),kind=kind,
                known_closed_position_ids=[t['position_id'] for t in closed],future_diagnostic_pnl=trade['pnl']))
        for group in groups.values():
            group['mean_net_r']=group.pop('net_r_sum')/group['count']
        extra=[e for e in events if e['kind']=='extra_brake']
        cases.append(dict(year=row['year'],cost=row['cost_multiplier'],sizing_reconstruction_checks=len(events),
            extra_brake_count=len(extra),extra_brake_frozen_parent_pnl=sum(e['future_diagnostic_pnl'] for e in extra),groups=dict(groups),events=events))
        print(row['year'],row['cost_multiplier'],'validated',len(events),'extra-brake N',len(extra),
              'frozen-parent PnL',round(sum(e['future_diagnostic_pnl'] for e in extra),2),flush=True)
    Path("data/directional-brake-diagnostics.json").write_text(json.dumps(dict(
        used_for_tuning=True,independent_validation=False,
        warning="Only closed histories are proposed inputs. Subsequent PnL is retrospective, not a feature or causal estimate; overlapping cost cases are not independent.",
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in (source,tape_path,Path(__file__))},cases=cases),indent=2),encoding="utf-8")


if __name__=="__main__":
    main()
