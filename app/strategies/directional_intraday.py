"""Symmetric signal-only extension for isolated perpetual research."""
from dataclasses import dataclass
from datetime import datetime, timezone

from app.data.models import Candle
from app.strategies.base import Action, Signal
from app.strategies.multitimeframe import completed_four_hour_closes


@dataclass(frozen=True)
class DirectionalSignal(Signal):
    direction: int = 0
    exit_long: bool = False
    exit_short: bool = False


class DirectionalIntradayStrategy:
    name = "perpetual_symmetric_intraday_research"
    minimum_atr_fraction = .006

    def entry_conditions(self,candles: list[Candle],fast: float,slow: float) -> tuple[bool,bool]:
        last=candles[-1]
        strong_long=last.close>last.open and last.close>=last.low+(last.high-last.low)*2/3
        strong_short=last.close<last.open and last.close<=last.low+(last.high-last.low)/3
        return (fast>slow and strong_long and last.close>max(c.high for c in candles[-21:-1]),
                fast<slow and strong_short and last.close<min(c.low for c in candles[-21:-1]))

    def generate(self, candles: list[Candle]) -> DirectionalSignal:
        if not candles:
            raise ValueError("completed history required")
        last = candles[-1]
        closes = completed_four_hour_closes(candles)
        direction, stop, exit_long, exit_short = 0, None, False, False
        if len(closes) == 60 and len(candles) >= 21:
            fast, slow = sum(closes[-20:])/20, sum(closes)/60
            exit_long = fast <= slow or last.close < min(c.low for c in candles[-11:-1])
            exit_short = fast >= slow or last.close > max(c.high for c in candles[-11:-1])
            ranges = [max(candles[i].high-candles[i].low, abs(candles[i].high-candles[i-1].close),
                          abs(candles[i].low-candles[i-1].close)) for i in range(len(candles)-14,len(candles))]
            atr = sum(ranges)/14
            if atr/last.close >= self.minimum_atr_fraction:
                long_entry,short_entry=self.entry_conditions(candles,fast,slow)
                if long_entry:
                    direction, stop = 1, last.close-2*atr
                elif short_entry:
                    direction, stop = -1, last.close+2*atr
                if stop is not None and stop <= 0:
                    direction, stop = 0, None
        action = Action.BUY if direction == 1 else Action.SELL if direction == -1 else Action.HOLD
        return DirectionalSignal(last.symbol,datetime.fromtimestamp(last.timestamp_ms/1000,timezone.utc),
            action,1.0 if direction else 0.0,self.name,stop_loss_price=stop,
            direction=direction,exit_long=exit_long,exit_short=exit_short)
