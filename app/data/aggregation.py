from app.data.models import Candle


def completed_four_hour_bars(hourly: list[Candle], count: int = 61) -> list[Candle]:
    """Reconstruct only complete UTC buckets from already completed hours."""
    result=[]
    for i in range(len(hourly)-1,2,-1):
        last=hourly[i]
        if last.timeframe!="1h":
            raise ValueError("hourly inputs required")
        if last.timestamp_ms%14400000!=10800000:
            continue
        group=hourly[i-3:i+1]
        if [c.timestamp_ms for c in group]!=list(range(last.timestamp_ms-10800000,last.timestamp_ms+1,3600000)):
            raise ValueError("incomplete four-hour bucket")
        result.append(Candle(last.exchange,last.symbol,"4h",group[0].timestamp_ms,group[0].open,
            max(c.high for c in group),min(c.low for c in group),last.close,sum(c.volume for c in group)))
        if len(result)==count:
            break
    return list(reversed(result))
