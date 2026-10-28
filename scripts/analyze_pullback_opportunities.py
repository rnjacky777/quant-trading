"""Count historical opportunities, not trades or forecast return space."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

from app.data.models import Candle
from app.strategies.directional_pullback import DirectionalPullbackStrategy
from app.strategies.multitimeframe import completed_four_hour_closes


def main() -> None:
    source=Path("data/btc-perpetual-1h/klines.json")
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(source.read_text())]
    groups=defaultdict(lambda:dict(hours=0,raw_long=0,raw_short=0,qualified_long=0,qualified_short=0,atr_fractions=[]))
    strategy=DirectionalPullbackStrategy()
    for i in range(243,len(tape)):
        current=tape[i]
        if current.timestamp_ms < 1704067200000:
            continue
        year=2024 if current.timestamp_ms < 1735689600000 else 2025
        h=tape[i-243:i+1]
        closes=completed_four_hour_closes(h)
        long,short=strategy.entry_conditions(h,sum(closes[-20:])/20,sum(closes)/60)
        g=groups[year];g['hours']+=1;g['raw_long']+=long;g['raw_short']+=short
        if not (long or short):
            continue
        atr=sum(max(h[j].high-h[j].low,abs(h[j].high-h[j-1].close),abs(h[j].low-h[j-1].close))
                for j in range(len(h)-14,len(h)))/14/current.close
        if atr>=.006:
            g['qualified_long']+=long;g['qualified_short']+=short;g['atr_fractions'].append(atr)
    for year,g in groups.items():
        values=g.pop('atr_fractions')
        g['median_qualified_atr_fraction']=median(values) if values else None
        g['median_one_atr_over_roundtrip_cost']=median(values)/.003 if values else None
        g['median_one_atr_over_double_roundtrip_cost']=median(values)/.006 if values else None
        print(year,json.dumps(g),flush=True)
    Path("data/pullback-opportunity-diagnostics.json").write_text(json.dumps(dict(
        source_sha256=sha256(source.read_bytes()).hexdigest(),years=dict(groups),
        note="Only entry-known completed data. ATR is realized volatility, not expected profit; ratios exclude funding and are not evidence of positive expectancy. Counts precede exits, risk and daily quota."),indent=2),encoding="utf-8")


if __name__=="__main__":
    main()
