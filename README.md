# Quant Trading System

Phase 1 implements historical, closed OHLCV candle ingestion and a read-only API. The project is separate from the LINE bot in the parent directory. It has no order submission code or exchange credentials.

## Architecture and data flow

`CCXT public OHLCV → provider interface → downloader validation → SQLite repository → FastAPI read API`

Modules are reserved for strategies, backtesting, risk, portfolio, execution, and monitoring. They will be implemented phase by phase. Strategy code will output signals and will never call an exchange. Risk will determine order size before execution is introduced.

## Setup

```powershell
cd quant-trading
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Environment variables in `.env.example` are documentation; defaults work without a file. Set variables in the shell or a secrets manager when overriding them. This first phase does not load `.env` automatically.

## Download candles

```powershell
python -m scripts.download --symbol BTC/USDT --timeframe 4h --since 2024-01-01T00:00:00+00:00 --until 2024-02-01T00:00:00+00:00
python -m scripts.download --symbol ETH/USDT --timeframe 1d --since 2024-01-01T00:00:00+00:00 --until 2024-02-01T00:00:00+00:00
```

`since` is inclusive and `until` is exclusive. Timestamps must include a UTC offset. Repeated imports update the same candle key. The downloader excludes the current, incomplete candle and rejects malformed or out of order data. It does not manufacture missing periods; inspect coverage before research.

## API and tests

```powershell
uvicorn app.api.main:app --reload
pytest
```

`GET /health` and `GET /candles?symbol=BTC%2FUSDT&timeframe=4h&limit=100` are read-only. The API does not trigger downloads.

## Roadmap

1. Historical data and quality checks (current phase)
2. Backtest engine with fees, slippage, and bias checks
3. SMA trend, momentum, and mean reversion baselines
4. Risk manager and position sizing
5. Paper execution
6. Exchange testnet adapter
7. Monitoring and strategy comparison
8. Small capital live trading, only after explicit opt-in and prior gates

Development, validation, and out-of-sample periods must be recorded before comparing strategies. An out-of-sample period loses that status after tuning against its results.
