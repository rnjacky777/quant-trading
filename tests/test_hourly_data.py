from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
import pytest

from app.api.main import app
from app.backtest.runs import BacktestRunRepository
from app.data.models import Candle
from app.data.repository import CandleRepository
from scripts.fetch_btc_hourly import parse_archive


@pytest.mark.parametrize("timestamp", [1704067200000, 1735689600000000])
def test_official_spot_archive_timestamp_units_are_normalized(timestamp):
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        archive.writestr("BTCUSDT.csv", f"{timestamp},100,102,99,101,3,0,0,0,0,0,0\n")
    candle = parse_archive(payload.getvalue())[0]
    assert candle.timestamp_ms == (timestamp // 1000 if timestamp >= 10**14 else timestamp)
    assert candle.timeframe == "1h"
    assert candle.close == 101


def test_hourly_data_can_be_selected_backtested_and_saved(tmp_path, monkeypatch):
    path = tmp_path / "hourly.sqlite3"
    start = 1704067200000
    candles = [Candle("binance", "BTC/USDT", "1h", start + i * 3600000,
                      100+i, 101+i, 99+i, 100+i, 1) for i in range(48)]
    CandleRepository(path).upsert(candles)
    monkeypatch.setenv("QUANT_DB_PATH", str(path))
    client = TestClient(app)
    assert '<option value="1h">1H</option>' in client.get("/").text
    response = client.get("/backtests/run", params=dict(strategy="sma", symbol="BTC/USDT", timeframe="1h",
        since="2024-01-01", until="2024-01-03", fast=2, slow=3, stop_loss_pct=5, risk_per_trade_pct=.5))
    assert response.status_code == 200
    assert response.context["saved_run"].timeframe == "1h"
    run = response.context["saved_run"]
    assert BacktestRunRepository(path).get_result(run.run_key)[0].timeframe == "1h"
