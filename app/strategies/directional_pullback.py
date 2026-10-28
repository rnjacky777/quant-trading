"""Symmetric trend pullback/reclaim entry; inherited exits and risk stay fixed."""
from app.data.models import Candle
from app.strategies.directional_intraday import DirectionalIntradayStrategy


class DirectionalPullbackStrategy(DirectionalIntradayStrategy):
    name = "perpetual_4h_trend_1h_mean_reclaim"

    def entry_conditions(self, candles: list[Candle], fast: float, slow: float) -> tuple[bool, bool]:
        if len(candles) < 21:
            return False, False
        last, previous = candles[-1], candles[-2]
        mean = sum(c.close for c in candles[-20:])/20
        previous_mean = sum(c.close for c in candles[-21:-1])/20
        return (
            fast > slow and previous.close < previous_mean and last.close > mean
            and last.close > last.open and last.close >= last.low+(last.high-last.low)*2/3,
            fast < slow and previous.close > previous_mean and last.close < mean
            and last.close < last.open and last.close <= last.low+(last.high-last.low)/3,
        )
