"""4h wave-trading signals; output timestamp remains the completed input hour."""
from datetime import datetime, timezone

from app.data.aggregation import completed_four_hour_bars
from app.data.models import Candle
from app.strategies.base import Action
from app.strategies.directional_intraday import DirectionalSignal


class DirectionalSwingStrategy:
    name="perpetual_symmetric_swing_research"

    def __init__(self, exit_lookback: int = 10) -> None:
        if type(exit_lookback) is not int or not 1 <= exit_lookback <= 59:
            raise ValueError("exit_lookback must be an integer from 1 to 59")
        self.exit_lookback = exit_lookback
        if exit_lookback != 10:
            self.name = f"perpetual_symmetric_swing_exit_{exit_lookback}_research"

    def entry_conditions(self, bars: list[Candle], fast: float, slow: float) -> tuple[bool, bool]:
        return (fast > slow and bars[-1].close > max(c.high for c in bars[-21:-1]),
                fast < slow and bars[-1].close < min(c.low for c in bars[-21:-1]))

    def generate(self,candles: list[Candle]) -> DirectionalSignal:
        if not candles:
            raise ValueError("completed history required")
        last=candles[-1]
        bars=completed_four_hour_bars(candles)
        direction,stop,exit_long,exit_short=0,None,False,False
        if len(bars)>=60:
            close=bars[-1].close
            fast=sum(c.close for c in bars[-20:])/20
            slow=sum(c.close for c in bars[-60:])/60
            exit_bars=bars[-self.exit_lookback-1:-1]
            exit_long=fast<=slow or close<min(c.low for c in exit_bars)
            exit_short=fast>=slow or close>max(c.high for c in exit_bars)
            if last.timestamp_ms%14400000==10800000:
                ranges=[max(bars[i].high-bars[i].low,abs(bars[i].high-bars[i-1].close),
                            abs(bars[i].low-bars[i-1].close)) for i in range(len(bars)-14,len(bars))]
                atr=sum(ranges)/14
                if atr/close>=.006:
                    long_entry, short_entry = self.entry_conditions(bars, fast, slow)
                    if long_entry:
                        direction,stop=1,close-2*atr
                    elif short_entry:
                        direction,stop=-1,close+2*atr
                    if stop is not None and stop<=0:
                        direction,stop=0,None
        return DirectionalSignal(last.symbol,datetime.fromtimestamp(last.timestamp_ms/1000,timezone.utc),
            Action.BUY if direction==1 else Action.SELL if direction==-1 else Action.HOLD,
            1 if direction else 0,self.name,stop_loss_price=stop,direction=direction,
            exit_long=exit_long,exit_short=exit_short)
