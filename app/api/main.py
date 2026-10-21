from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.candles import router as candles_router
from app.api.routes.dashboard import router as dashboard_router

app = FastAPI(title="Quant Trading Research API", version="0.1.0")
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parent / "static"),
    name="static",
)
app.include_router(dashboard_router)
app.include_router(candles_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
