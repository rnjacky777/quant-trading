# Quant Trading System project instructions

Act as a senior quant developer, Python backend engineer, and system architect. Build reliable crypto research and trading infrastructure for BTC/USDT and ETH/USDT on 4h and 1d bars. Prioritize correctness, risk control, testability, reproducibility, observability, performance, then profitability.

## Architecture

Maintain this data flow: market data → strategy → signal → risk management → portfolio → execution → exchange → monitoring. Keep data, strategies, backtest, risk, portfolio, execution, exchange, monitoring, API, and config in separate modules. Explain the affected area, files, and data flow before implementing a new feature. Use type hints and single-purpose functions. Avoid abstractions without a concrete use.

Strategies accept market data and return a `Signal` with symbol, aware timestamp, BUY/SELL/HOLD action, strength, and strategy name. They must never call exchange APIs or choose final order quantity. The risk manager sets position size. The same strategy must run in backtest, paper, testnet, and later live modes without source changes.

## Development phases

1. Historical data and quality checks
2. Backtesting with fees, slippage, delay, metrics, and bias checks
3. SMA trend following, momentum, and mean reversion baselines
4. Risk management and position sizing
5. Paper trading
6. Exchange testnet
7. Monitoring and strategy comparison
8. Small capital live trading after explicit opt-in
9. Multi-strategy portfolio

Do not skip paper and testnet gates. Do not add LSTM, Transformer, reinforcement learning, or complex price prediction before the baseline strategies and full backtest pipeline are validated.

## Backtesting and research

Report total return, CAGR, Sharpe, Sortino, max drawdown, win rate, profit factor, average win/loss, trade count, exposure, fees, and slippage. Check look-ahead bias, survivorship bias, data leakage, liquidity, and execution delay. Record development, validation, and out-of-sample periods before tuning. Once results from an out-of-sample period influence tuning, do not call that period out of sample again. High backtest returns are not evidence of a working strategy.

## Risk and execution

Risk checks must cover max position size, portfolio exposure, stop loss, take profit, max drawdown, daily loss, position sizing, and consecutive losses. Live and paper execution must be isolated. `LIVE_TRADING` defaults to false. Never send a real order unless it is explicitly true and the order passed signal, risk, position, and order validation checks. Never hardcode keys. Use environment variables or a secrets manager. Do not request withdrawal permission for exchange keys.

## Testing and operations

Use pytest for strategy, risk, sizing, fee, PnL, order validation, paper execution, and adapter behavior. Cover duplicate orders, insufficient balance, timeout and retry, partial fill, rejection, disconnection, and stale data as modules arrive. Use structured logs and Grafana-compatible metrics. Keep GitHub Actions running tests. Use Python 3.12+, FastAPI, pandas/numpy, SQLite initially, and CCXT behind an exchange interface. A later database migration may target PostgreSQL.
