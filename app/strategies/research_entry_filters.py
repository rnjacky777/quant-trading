"""Literature-inspired entry ablations, preserving both long and short exits."""
from dataclasses import replace
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.data.models import Candle
from app.strategies.base import Action
from app.strategies.directional_intraday import DirectionalIntradayStrategy, DirectionalSignal


def monday_asia_entry_window(timestamp_ms: int) -> bool:
    """Sunday19:00 through Monday19:00 New York, exclusive end; handles DST."""
    local = datetime.fromtimestamp(timestamp_ms/1000, timezone.utc).astimezone(ZoneInfo("America/New_York"))
    return local.weekday()==6 and local.hour>=19 or local.weekday()==0 and local.hour<19


class ResearchEntryFilter:
    def __init__(self, strategy: DirectionalIntradayStrategy, variant: str) -> None:
        if variant not in {"asia_session", "volume_confirmation"}:
            raise ValueError("unknown research entry filter")
        self.strategy, self.variant = strategy, variant
        self.name = f"{strategy.name}_{variant}"

    def generate(self, candles: list[Candle]) -> DirectionalSignal:
        signal = self.strategy.generate(candles)
        permitted = True
        if signal.direction:
            if self.variant=="asia_session":
                permitted=monday_asia_entry_window(candles[-1].timestamp_ms+3600000)
            else:
                permitted=len(candles)>=21 and candles[-1].volume>sum(c.volume for c in candles[-21:-1])/20
        if not permitted:
            signal=replace(signal,action=Action.HOLD,direction=0,strength=0,stop_loss_price=None)
        return replace(signal,strategy_name=self.name)
