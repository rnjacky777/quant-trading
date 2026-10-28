from datetime import datetime, timezone
from dataclasses import replace

import pytest

from app.data.models import Candle
from app.strategies.base import Action
from app.strategies.directional_intraday import DirectionalSignal
from app.strategies.research_entry_filters import ResearchEntryFilter, monday_asia_entry_window


def ms(value):
    return int(datetime.fromisoformat(value).timestamp()*1000)


@pytest.mark.parametrize("time,expected", [
    ("2024-01-07T23:00:00+00:00",False),
    ("2024-01-08T00:00:00+00:00",True),
    ("2024-01-09T00:00:00+00:00",False),
    ("2024-07-07T22:00:00+00:00",False),
    ("2024-07-07T23:00:00+00:00",True),
    ("2024-07-08T22:00:00+00:00",True),
    ("2024-07-08T23:00:00+00:00",False),
])
def test_session_window_handles_both_dst_regimes_and_exclusive_end(time,expected):
    assert monday_asia_entry_window(ms(time)) is expected


class Stub:
    name="test_directional"
    def __init__(self,direction):
        self.direction=direction
    def generate(self,bars):
        d=self.direction
        return DirectionalSignal("BTC/USDT",datetime.fromtimestamp(bars[-1].timestamp_ms/1000,timezone.utc),
            Action.BUY if d==1 else Action.SELL,1,self.name,stop_loss_price=90 if d==1 else 110,
            direction=d,exit_long=True,exit_short=True)


@pytest.mark.parametrize("direction", [-1,1])
def test_volume_gate_uses_only_previous_volume_and_preserves_both_exits(direction):
    bars=[Candle("test","BTC/USDT","1h",i*3600000,100,100,100,100,1) for i in range(21)]
    strategy=ResearchEntryFilter(Stub(direction),"volume_confirmation")
    blocked=strategy.generate(bars)
    assert blocked.direction==0 and blocked.action is Action.HOLD
    assert blocked.exit_long and blocked.exit_short
    bars[-1]=replace(bars[-1],volume=1.1)
    assert strategy.generate(bars).direction==direction


def test_session_uses_known_execution_time_not_the_hourly_open_label():
    candle=Candle("test","BTC/USDT","1h",ms("2024-01-07T23:00:00+00:00"),100,100,100,100,1)
    strategy=ResearchEntryFilter(Stub(-1),"asia_session")
    assert strategy.generate([candle]).direction==-1  # Closed at Monday00 UTC.
    blocked=strategy.generate([replace(candle,timestamp_ms=candle.timestamp_ms-3600000)])
    assert blocked.direction==0 and blocked.exit_long and blocked.exit_short
