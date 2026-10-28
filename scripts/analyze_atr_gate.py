"""Causal opportunity counts only, not hypothetical portfolio returns."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

from app.data.models import Candle
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.sweep_no_atr_floor import DirectionalSweepNoAtrFloorStrategy


def main() -> None:
    path=Path('data/btc-perpetual-1h/klines.json')
    tape=[Candle('binance-usdm','BTC/USDT','1h',int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(path.read_text())]
    groups=defaultdict(list)
    parent=DirectionalSweepStructureConfirmStrategy();child=DirectionalSweepNoAtrFloorStrategy()
    for year,start,end in ((2024,1704067200000,1735689600000),(2025,1735689600000,1767225600000)):
        period=[c for c in tape if start-243*3600000<=c.timestamp_ms<end]
        for i,c in enumerate(period):
            if c.timestamp_ms<start or i==0:continue
            history=period[:i];signal=child.generate(history)
            if not signal.direction:continue
            old=parent.generate(history)
            if old.direction:
                assert old.direction==signal.direction and old.stop_loss_price==signal.stop_loss_price
            # Distance at the known confirmation close; not execution or profit.
            groups[(year,signal.direction,bool(old.direction))].append(abs(history[-1].close-signal.stop_loss_price)/history[-1].close)
    rows=[dict(year=k[0],direction=k[1],passes_original_atr_floor=k[2],raw_signals=len(v),
        median_structural_stop_fraction=median(v)) for k,v in groups.items()]
    out=dict(candles_sha256=sha256(path.read_bytes()).hexdigest(),used_for_tuning=True,
        warning='Raw signals before quota, invalidated opening gaps, shared risk and exits; not fills or returns.',rows=rows)
    Path('data/atr-gate-diagnostics.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
