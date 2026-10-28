from datetime import datetime, timezone

import pytest

from app.backtest.frequency import entry_frequency


def trade(day, sleeve="intraday", side=1):
    stamp=int(datetime(2024,1,day,tzinfo=timezone.utc).timestamp()*1000)
    return dict(entry_timestamp_ms=stamp,exit_timestamp_ms=stamp+86400000,
                sleeve=sleeve,direction=side)


def test_frequency_uses_entry_days_calendar_denominator_and_sleeve_counts():
    f=entry_frequency([trade(1),trade(1,side=-1),trade(2,"swing")],2024)
    assert f['total']==3 and f['calendar_days']==366
    assert f['active_days']==2 and f['zero_entry_days']==364
    assert f['intraday']==2 and f['intraday_active_days']==1
    assert f['intraday_daily_average']==pytest.approx(2/366)
    assert entry_frequency([],2025)['zero_entry_days']==365
    with pytest.raises(ValueError):
        entry_frequency([trade(1)],2025)
