"""Identify where structural stops narrowed risk distance and changed outcomes."""
from bisect import bisect_left
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path

from app.data.models import Candle
from app.strategies.pa_smc import DirectionalSweepStrategy


def main() -> None:
    source=Path("data/perpetual-sweep-structural-stop.json")
    reference=Path("data/perpetual-confirmed-efficiency.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape]
    refs={(r['year'],r['cost_multiplier']):r for r in json.loads(reference.read_text())['rows']}
    rows=json.loads(source.read_text())['rows'];cases=[]
    if len(rows)!=4 or {(r['year'],r['cost_multiplier']) for r in rows}!=set(refs):
        raise ValueError("all four unique cases required")
    for row in rows:
        ref=refs[(row['year'],row['cost_multiplier'])]
        if row['input_fingerprints']!=ref['input_fingerprints']:
            raise ValueError("mismatched evidence")
        originals={(t['entry_timestamp_ms'],t['sleeve'],t['direction']):t for t in ref['result']['trades']}
        start=1704067200000 if row['year']==2024 else 1735689600000
        warmup=bisect_left(times,start-243*3600000)
        groups=defaultdict(lambda:dict(count=0,pnl=0.,fees=0.,stop_exits=0,net_r_sum=0.,reference_matched_pnl=0.,reference_matched_count=0))
        events=[]
        for t in row['result']['trades']:
            if t['sleeve']!='intraday':
                continue
            index=bisect_left(times,t['entry_timestamp_ms'])
            old=DirectionalSweepStrategy().generate(tape[warmup:index])
            if old.direction!=t['direction']:
                raise ValueError("old raw signal differs")
            narrower=t['direction']*(t['stop_loss_price']-old.stop_loss_price)>0
            group=f"{t['direction']}/{'narrower_than_2atr' if narrower else 'wider_or_equal'}"
            g=groups[group];g['count']+=1;g['pnl']+=t['pnl'];g['fees']+=t['fees'];g['stop_exits']+=t['exit_reason']=='stop_loss'
            g['net_r_sum']+=t['pnl']/t['planned_risk']
            match=originals.get((t['entry_timestamp_ms'],t['sleeve'],t['direction']))
            if match:
                g['reference_matched_pnl']+=match['pnl'];g['reference_matched_count']+=1
            events.append(dict(position_id=t['position_id'],direction=t['direction'],narrower_than_2atr=narrower,
                atr_stop=old.stop_loss_price,structural_stop=t['stop_loss_price'],pnl=t['pnl'],fees=t['fees'],
                original_pnl=match['pnl'] if match else None,exit_reason=t['exit_reason']))
        for g in groups.values():
            g['mean_net_r']=g.pop('net_r_sum')/g['count']
        cases.append(dict(year=row['year'],cost=row['cost_multiplier'],groups=dict(groups),events=events))
        print(row['year'],row['cost_multiplier'],json.dumps(dict(groups)),flush=True)
    Path("data/structural-risk-diagnostics.json").write_text(json.dumps(dict(
        used_for_tuning=True,independent_validation=False,
        warning="Reference cohorts are matched historical paths with different sizing and loss streaks, not causal policy estimates.",
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in (source,reference,tape_path,Path(__file__))},cases=cases),indent=2),encoding="utf-8")


if __name__=="__main__":
    main()
