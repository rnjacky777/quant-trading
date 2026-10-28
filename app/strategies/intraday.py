"""Fixed, interpretable BTC hourly research baseline; no sizing or execution."""
from datetime import datetime, timezone
from math import isfinite

from app.data.models import Candle
from app.strategies.base import Action, Signal
from app.strategies.multitimeframe import completed_four_hour_closes


class IntradayTrendStrategy:
    def __init__(self, entry: str = "breakout", min_atr_fraction: float = 0.0, strong_close: bool = False) -> None:
        if entry not in {"breakout", "pullback"}:
            raise ValueError("invalid intraday entry mode")
        self.entry = entry
        if not isfinite(min_atr_fraction) or not 0 <= min_atr_fraction < 1:
            raise ValueError("invalid ATR fraction")
        self.min_atr_fraction = min_atr_fraction
        self.strong_close = strong_close
        self.name = f"intraday_{entry}"

    def generate(self, candles: list[Candle]) -> Signal:
        if not candles:
            raise ValueError("strategy needs history")
        last = candles[-1]
        closes = completed_four_hour_closes(candles)
        action = Action.HOLD
        stop = None
        if len(closes) == 60 and len(candles) >= 21:
            trend = sum(closes[-20:])/20 > sum(closes)/60
            exit_level = min(c.low for c in candles[-11:-1])
            if not trend or last.close < exit_level:
                action = Action.SELL
            else:
                breakout = last.close > max(c.high for c in candles[-21:-1])
                mean = sum(c.close for c in candles[-20:])/20
                previous_mean = sum(c.close for c in candles[-21:-1])/20
                reclaim = candles[-2].close < previous_mean and last.close > mean
                entry_trigger = breakout if self.entry == "breakout" else reclaim
                if self.strong_close:
                    entry_trigger = (entry_trigger and last.close > last.open
                                     and last.close >= last.low+(last.high-last.low)*2/3)
                if entry_trigger:
                    ranges = [max(candles[i].high-candles[i].low,
                                  abs(candles[i].high-candles[i-1].close),
                                  abs(candles[i].low-candles[i-1].close)) for i in range(len(candles)-14, len(candles))]
                    # Simple ATR14, not Wilder smoothing; all inputs are completed.
                    atr = sum(ranges)/14
                    stop = last.close - 2*atr
                    if 0 < stop < last.close and atr/last.close >= self.min_atr_fraction:
                        action = Action.BUY
                    else:
                        stop = None
        return Signal(last.symbol, datetime.fromtimestamp(last.timestamp_ms/1000, timezone.utc),
                      action, 1.0 if action is Action.BUY else 0.0, self.name, stop_loss_price=stop)
