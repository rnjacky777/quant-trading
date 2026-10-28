"""Attribute actual signal exits to channel-only versus completed 4H reversal."""
from bisect import bisect_left
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path

from app.data.models import Candle
from app.strategies.multitimeframe import completed_four_hour_closes


def main() -> None:
    source=Path("data/perpetual-directional-loss-guard.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[]
    rows=json.loads(source.read_text())['rows']
    if len(rows)!=4 or {(r['year'],r['cost_multiplier']) for r in rows}!={(2024,1),(2024,2),(2025,1),(2025,2)}:
        raise ValueError("all four unique periods/costs required")
    for row in rows:
        warmup=bisect_left(times,(1704067200000 if row['year']==2024 else 1735689600000)-243*3600000)
        groups=defaultdict(lambda:dict(count=0,pnl=0.,remaining_hours_sum=0.));events=[]
        for trade in row['result']['trades']:
            if trade['sleeve']!='intraday' or trade['exit_reason']!='signal':
                continue
            i=bisect_left(times,trade['exit_timestamp_ms']);history=tape[warmup:i]
            closes=completed_four_hour_closes(history)
            fast,slow=sum(closes[-20:])/20,sum(closes)/60
            trend_valid=trade['direction']*(fast-slow)>0
            channel_exit=history[-1].close<min(c.low for c in history[-11:-1]) if trade['direction']==1 else history[-1].close>max(c.high for c in history[-11:-1])
            if trend_valid and not channel_exit:
                raise ValueError("signal exit is not explained by original rules")
            kind='channel_only' if trend_valid else '4h_reversal'
            remaining=24-(trade['exit_timestamp_ms']-trade['entry_timestamp_ms'])/3600000
            group=groups[f"{trade['direction']}/{kind}"]
            group['count']+=1;group['pnl']+=trade['pnl'];group['remaining_hours_sum']+=remaining
            events.append(dict(position_id=trade['position_id'],direction=trade['direction'],kind=kind,
                pnl=trade['pnl'],fast_4h=fast,slow_4h=slow,remaining_hours=remaining))
        for group in groups.values():
            group['mean_remaining_hours']=group.pop('remaining_hours_sum')/group['count']
        cases.append(dict(year=row['year'],cost=row['cost_multiplier'],groups=dict(groups),events=events))
    Path("data/channel-exit-diagnostics.json").write_text(json.dumps(dict(used_for_tuning=True,
        independent_validation=False,warning="Retrospective exit cohorts; removing a loss exit is not a guaranteed recovery.",
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in (source,tape_path,Path(__file__))},cases=cases),indent=2),encoding="utf-8")
    print("Saved all four actual exit-attribution cases.")


if __name__=="__main__":
    main()
