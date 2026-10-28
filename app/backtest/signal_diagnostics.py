"""Fixed-horizon event study; explicitly not a stop-managed portfolio backtest."""
from collections import defaultdict
from statistics import mean, median

from app.data.models import Candle, FundingRate


HORIZONS = (4,12,24)


def horizon_outcome(entry: Candle, exit_bar: Candle | None, direction: int, *,
                    fee_bps: float, slippage_bps: float, funding: list[FundingRate]) -> dict:
    """Unit entry-fill notional; entry-open funding excluded, exit-open included."""
    if direction not in {-1,1} or not 0<=fee_bps<10000 or not 0<=slippage_bps<10000:
        raise ValueError("invalid event direction or execution costs")
    if exit_bar is None:
        return dict(status="censored",reason="insufficient_same_year_future")
    if exit_bar.timestamp_ms<=entry.timestamp_ms:
        raise ValueError("forward endpoint must follow entry")
    fee,slip=fee_bps/10000,slippage_bps/10000
    entry_fill=entry.open*(1+direction*slip)
    exit_fill=exit_bar.open*(1-direction*slip)
    gross=direction*(exit_bar.open-entry.open)/entry_fill
    slippage=(abs(entry_fill-entry.open)+abs(exit_fill-exit_bar.open))/entry_fill
    fees=(entry_fill+exit_fill)*fee/entry_fill
    funding_return=sum(-direction*f.rate*f.mark_price for f in funding
                       if entry.timestamp_ms<f.timestamp_ms<=exit_bar.timestamp_ms)/entry_fill
    return dict(status="observed",entry_timestamp_ms=entry.timestamp_ms,exit_timestamp_ms=exit_bar.timestamp_ms,
        entry_reference=entry.open,entry_fill=entry_fill,
        exit_reference=exit_bar.open,exit_fill=exit_fill,gross_return=gross,
        reference_price_return=direction*(exit_bar.open-entry.open)/entry.open,
        slippage_fraction=slippage,fee_fraction=fees,funding_return=funding_return,
        net_return=gross-slippage-fees+funding_return)


def summarize_signals(events: list[dict]) -> list[dict]:
    """Keep direction, sleeve and selection reason distinct; never sum returns."""
    groups: dict[tuple,list[dict]]=defaultdict(list)
    for event in events:
        state=event['outcome']['status'];reason=event['outcome']['reason']
        scopes={"all",state,f"reason:{reason}"}
        for scope in scopes:
            groups[(event['sleeve'],event['direction'],scope)].append(event)
    result=[]
    for (sleeve,side,scope),items in sorted(groups.items()):
        for hours in HORIZONS:
            observed=[e for e in items if e['horizons'][str(hours)]['status']=='observed']
            values=[e['horizons'][str(hours)] for e in observed]
            independent_windows=[];next_start=-1
            for event in sorted(observed,key=lambda e:e['timestamp_ms']):
                if event['timestamp_ms']>=next_start:
                    independent_windows.append(event['horizons'][str(hours)]['net_return'])
                    next_start=event['timestamp_ms']+hours*3600000
            row=dict(sleeve=sleeve,direction=side,scope=scope,hours=hours,
                signal_count=len(items),observed_count=len(values),censored_count=len(items)-len(values),
                unique_entry_days=len({e['timestamp_ms']//86400000 for e in observed}),
                nonoverlap_count=len(independent_windows),
                nonoverlap_mean_net=mean(independent_windows) if independent_windows else None)
            for key in ('net_return','gross_return','reference_price_return','slippage_fraction','fee_fraction','funding_return'):
                row[f"mean_{key}"]=mean(v[key] for v in values) if values else None
            row['median_net_return']=median(v['net_return'] for v in values) if values else None
            row['positive_fraction']=mean(v['net_return']>0 for v in values) if values else None
            result.append(row)
    return result
