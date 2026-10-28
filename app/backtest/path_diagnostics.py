"""Retrospective diagnostics; never consumed by strategy entry decisions."""
from collections import defaultdict
from datetime import datetime, timezone

from app.data.models import Candle


def monthly_equity(result: dict, year: int) -> list[dict]:
    """Month-end hourly snapshot changes, including open-position mark-to-market."""
    ends: dict[int, float] = {}
    stamps=[p['timestamp_ms'] for p in result['equity_curve']]
    if stamps!=sorted(stamps) or len(set(stamps))!=len(stamps):
        raise ValueError("equity snapshots must be ordered and unique")
    for point in result['equity_curve']:
        date=datetime.fromtimestamp(point['timestamp_ms']/1000,timezone.utc)
        if date.year==year:
            ends[date.month]=point['equity']
    if set(ends)!=set(range(1,13)):
        raise ValueError("all twelve months of equity evidence required")
    settlements: dict[int, float] = defaultdict(float)
    for trade in result['trades']:
        date=datetime.fromtimestamp(trade['exit_timestamp_ms']/1000,timezone.utc)
        if date.year==year:
            settlements[date.month]+=trade['pnl']
    prior=result['initial_cash'];rows=[]
    for month in range(1,13):
        end=ends[month]
        rows.append(dict(month=f"{year}-{month:02}",start_equity=prior,end_equity=end,
            equity_change=end-prior,return_fraction=end/prior-1 if prior>0 else None,
            closed_trade_pnl=settlements[month]))
        prior=end
    return rows


def completed_close_path(trade: dict, candles: list[Candle]) -> dict:
    """Exclude the exit bar: its path may occur after an open/stop exit."""
    distance=abs(trade['entry_price']-trade['stop_loss_price'])
    if distance<=0:
        raise ValueError("positive initial stop distance required")
    changes=[trade['direction']*(c.close-trade['entry_price'])/distance for c in candles
             if trade['entry_timestamp_ms']<=c.timestamp_ms<trade['exit_timestamp_ms']]
    return dict(completed_hours=len(changes),max_favorable_close_r=max([0.]+changes),
        max_adverse_close_r=max([0.]+[-v for v in changes]),
        lost_after_1r_close=trade['pnl']<0 and any(v>=1 for v in changes),
        last_completed_close_r=changes[-1] if changes else None)
