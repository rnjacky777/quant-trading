"""UTC entry frequency, separate from concurrent positions and exit counts."""
from calendar import isleap
from collections import Counter
from datetime import datetime, timezone


def entry_frequency(trades: list[dict], year: int) -> dict:
    days = 366 if isleap(year) else 365
    counts: Counter = Counter()
    active: set[int] = set()
    short_active: set[int] = set()
    for trade in trades:
        stamp = trade["entry_timestamp_ms"]
        if datetime.fromtimestamp(stamp/1000, timezone.utc).year != year:
            raise ValueError("entry outside declared calendar year")
        sleeve = trade.get("sleeve", "single")
        counts[(sleeve, trade["direction"])] += 1
        active.add(stamp//86400000)
        if sleeve == "intraday":
            short_active.add(stamp//86400000)
    intraday = sum(counts[("intraday", side)] for side in (1, -1))
    return dict(total=len(trades), calendar_days=days, daily_average=len(trades)/days,
        active_days=len(active), zero_entry_days=days-len(active), intraday=intraday,
        intraday_daily_average=intraday/days, intraday_active_days=len(short_active),
        groups=[dict(sleeve=sleeve, direction=side, count=counts[(sleeve, side)],
                     daily_average=counts[(sleeve, side)]/days)
                for sleeve in ("intraday", "swing", "single") for side in (1, -1)
                if sleeve != "single" or counts[(sleeve, side)]])
