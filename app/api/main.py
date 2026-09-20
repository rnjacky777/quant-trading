from fastapi import FastAPI

from app.api.routes.candles import router as candles_router

app = FastAPI(title="Quant Trading Research API", version="0.1.0")
app.include_router(candles_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
