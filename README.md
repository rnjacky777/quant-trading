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

Open `http://127.0.0.1:8000/` for the research dashboard. It shows available
market data and provides a form for running SMA trend or buy-and-hold backtests.
Results include the equity curve, performance metrics, and trade history. The
dashboard can download public closed candles and delete one symbol/timeframe
dataset after browser confirmation. It is research-only and cannot submit paper
or live orders.

Successful dashboard backtests are stored as reproducible experiment records in
SQLite. Strategy versions and backtest experiments are separate records. A new
strategy version is created only when the signal or risk parameters change:
SMA periods, stop loss, take profit, or leverage. Changing dates, research stage,
market data, initial cash, fees, or slippage creates another experiment under the
same strategy version. Identical experiments reuse the existing record without
changing its creation time, and the dashboard shows a duplicate warning. Fixed stops and targets use candle high/low; if both are touched in
one candle, the conservative stop-first assumption is used.

## Baseline backtest

The first backtest is a long/cash SMA trend baseline. A signal uses a completed candle and executes at the next candle's open. Fees and adverse slippage are charged on entry and exit. Strategy code emits only BUY/SELL/HOLD; allocation remains outside the strategy.

Indicator backtests load the required candles before the requested start date as
warm-up history. Warm-up candles can influence signals, but orders and performance
measurement begin only at the requested start. The result page reports how many
warm-up candles were available so a short date range does not silently produce
misleading zero-trade results.

```powershell
python -m scripts.backtest --symbol BTC/USDT --timeframe 1d `
  --since 2020-01-01T00:00:00+00:00 --until 2025-01-01T00:00:00+00:00 `
  --fast 20 --slow 60 --fee-bps 10 --slippage-bps 5

# Comparison benchmark
python -m scripts.backtest --strategy buy-hold --symbol BTC/USDT --timeframe 1d `
  --since 2020-01-01T00:00:00+00:00 --until 2025-01-01T00:00:00+00:00
```

The command reports total return, CAGR, Sharpe, Sortino, maximum drawdown, win rate, profit factor, average win/loss, trade count, exposure, fees, and modeled slippage. It rejects missing candle intervals rather than silently backtesting incomplete data. The final open position is liquidated at the last close with costs.

## Perpetual futures accounting

The backtest core accepts explicit `FundingRate`, `MarkPriceCandle`, and
Binance-style `MarginBracket` datasets for isolated-margin perpetual tests.
Perpetual mode refuses to run unless all three inputs are present. Funding is
settled at the recorded timestamp, liquidation uses Mark Price and maintenance
margin brackets, and results report net funding, liquidation fees/count, and
maximum margin ratio. `DerivativesRepository` stores these inputs and versioned
bracket snapshots in SQLite for reproducible runs.

The dashboard currently runs spot datasets while the authenticated Binance
USD-M bracket synchronizer is pending. It does not substitute spot close prices
or zero funding for a futures result.

## Roadmap

The delivery plan has three user-visible workflows: historical backtesting, daily paper trading, then exchange testnet followed by explicitly enabled small-capital live trading. See [docs/ROADMAP.md](docs/ROADMAP.md) for gates and safety controls.

Development, validation, and out-of-sample periods must be recorded before comparing strategies. An out-of-sample period loses that status after tuning against its results.
