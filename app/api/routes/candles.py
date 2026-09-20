from fastapi import APIRouter, HTTPException, Query

from app.config.settings import Settings
from app.data.repository import CandleRepository

router = APIRouter()


@router.get("/candles")
def get_candles(
    symbol: str,
    timeframe: str,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict]:
    settings = Settings.from_env()
    try:
        candles = CandleRepository(settings.db_path).list_candles(
            settings.exchange_id, symbol, timeframe, limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return [vars(candle) for candle in candles]
