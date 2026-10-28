"""Separate price edge, net payoff and repeated entries without changing costs."""
from bisect import bisect_left
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path

from app.data.models import Candle
from app.strategies.multitimeframe import completed_four_hour_closes


def main() -> None:
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape];episodes={};episode=0;previous=None
    for i in range(243,len(tape)):
        closes=completed_four_hour_closes(tape[i-243:i+1])
        difference=sum(closes[-20:])/20-sum(closes)/60
        side=1 if difference>0 else -1 if difference<0 else 0
        if side!=previous:
            episode+=1;previous=side
        episodes[tape[i].timestamp_ms]=episode
    paths=[Path("data/perpetual-confirmed-efficiency.json"),Path("data/perpetual-directional-pullback.json")]
    cases=[]
    for path in paths:
        for row in json.loads(path.read_text())['rows']:
            ts=row['result']['trades'];m=row['result']['metrics'];seen=set()
            groups=defaultdict(lambda:dict(count=0,pnl=0.,fees=0.,funding=0.,price_pnl_after_slippage=0.))
            for t in sorted(ts,key=lambda t:t['entry_timestamp_ms']):
                prior_index=bisect_left(times,t['entry_timestamp_ms'])-1
                context=episodes[times[prior_index]]
                key=(t['sleeve'],t['direction'],context)
                repeat=key in seen;seen.add(key)
                labels=[f"{t['sleeve']}/{'long' if t['direction']==1 else 'short'}/{'repeat' if repeat else 'first'}",
                        f"{t['sleeve']}/exit/{t['exit_reason']}"]
                for label in labels:
                    g=groups[label];g['count']+=1;g['pnl']+=t['pnl'];g['fees']+=t['fees'];g['funding']+=t['funding']
                    g['price_pnl_after_slippage']+=t['pnl']+t['fees']-t['funding']
            price=sum(t['pnl']+t['fees']-t['funding'] for t in ts)
            loss=abs(m['average_loss']);denom=m['average_win']+loss
            evidence=dict(source=str(path),year=row['year'],cost=row['cost_multiplier'],
                net_pnl=sum(t['pnl'] for t in ts),executed_price_pnl_before_fees_funding=price,
                fees=sum(t['fees'] for t in ts),funding=sum(t['funding'] for t in ts),
                actual_win_rate=m['win_rate'],sample_payoff_break_even_win_rate=loss/denom if denom else None,
                groups=dict(groups))
            cases.append(evidence)
            if row['cost_multiplier']==1:
                print(path.name,row['year'],'net',round(evidence['net_pnl'],2),'price',round(price,2),
                      'win',round(m['win_rate'],3),'sample_break_even',round(loss/denom,3))
                print([(k,v['count'],round(v['pnl'],2)) for k,v in groups.items() if '/exit/' not in k])
    Path("data/profit-failure-diagnostics.json").write_text(json.dumps(dict(
        note="Executed-price PnL still includes slippage; not a zero-cost rerun. Sample break-even rate is a descriptive identity, not a predicted required win rate. Repeat=another same-sleeve/side accepted entry within unchanged completed-4h SMA20/60 sign, not necessarily concurrent. Overlapping groups/cost cases are not independent.",
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in paths+[tape_path,Path(__file__)]},cases=cases),indent=2),encoding="utf-8")


if __name__=="__main__":
    main()
