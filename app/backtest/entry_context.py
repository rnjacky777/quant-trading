"""Entry-known extension versus completed 4H mean; open gap is execution-time."""
from app.data.aggregation import completed_four_hour_bars
from app.data.models import Candle


def entry_context(candles: list[Candle], direction: int, entry_open: float) -> dict:
    if direction not in {-1,1} or entry_open<=0 or len(candles)<15:
        raise ValueError("valid direction, entry open and completed history required")
    bars=completed_four_hour_bars(candles)
    if len(bars)<21:
        raise ValueError("at least 21 completed 4h bars required")
    def atr(tape: list[Candle]) -> float:
        return sum(max(tape[i].high-tape[i].low,abs(tape[i].high-tape[i-1].close),
                       abs(tape[i].low-tape[i-1].close)) for i in range(len(tape)-14,len(tape)))/14
    hourly_atr,four_hour_atr=atr(candles),atr(bars)
    if min(hourly_atr,four_hour_atr)<=0:
        raise ValueError("positive realized ranges required")
    fast=sum(c.close for c in bars[-20:])/20
    last=candles[-1]
    extension=direction*(last.close-fast)/four_hour_atr
    bucket=("at_or_behind_mean" if extension<=0 else "0_to_1_atr" if extension<=1
            else "1_to_2_atr" if extension<=2 else "above_2_atr")
    gap=direction*(entry_open-last.close)
    return dict(signal_close=last.close,completed_4h_sma20=fast,completed_4h_atr14=four_hour_atr,
        completed_1h_atr14=hourly_atr,signed_extension_4h_atr=extension,extension_bucket=bucket,
        execution_gap_bps=gap/last.close*10000,execution_gap_1h_atr=gap/hourly_atr,
        gap_bucket="adverse" if gap>0 else "non_adverse")
