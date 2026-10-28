# Delivery roadmap

The product is organized around three user-visible workflows. Risk checks, persistence, monitoring, and tests are mandatory parts of each workflow rather than separate destinations.

## 1. Historical backtesting

Status: baseline implemented.

- Closed-candle data from CCXT into SQLite
- Long/cash event-driven simulation
- Signal on completed candle, execution at next open
- Trading fee and adverse slippage on both sides
- SMA trend and buy-and-hold benchmark
- Momentum and mean-reversion baselines through CLI and dashboard
- Persisted experiment and risk/exit policy identities, including CLI runs
- Cost-aware per-trade risk sizing, cash and single-market exposure caps at 1x
- Fixed-target vs strategy-signal exits with protective stops
- Immutable research windows and consumed-holdout checks
- Continuous annual performance attribution
- Free-form version/date backtesting with immutable saved-version settings
- Version-level waiting-AI queue, complete evidence audit and per-period child comparisons
- Return, CAGR, Sharpe, Sortino, drawdown, trade, exposure, fee, and slippage metrics
- Reject incomplete candle sequences

Next gates:

- ATR/support-based invalidation rules and portfolio-wide risk limits
- Drawdown, daily-loss and consecutive-loss circuit breakers
- Add parameter sensitivity and walk-forward comparison
- Add portfolio backtests for BTC/ETH

## 2. Daily paper trading

Status: next implementation target.

- Scheduled closed-candle update
- Generate one idempotent signal per symbol/timeframe/candle
- Risk manager determines size
- Paper execution with cash, positions, fees, slippage, and trade ledger
- Reject duplicate orders and stale market data
- Daily portfolio snapshot and reconciliation
- Alerts and structured logs

Exit gate: at least 90 days of forward paper results with no unresolved reconciliation or duplicate-order defects.

## 3. Testnet and small-capital live trading

Status: blocked by the paper-trading gate by design.

Sequence:

1. Exchange testnet using the same order and risk interfaces
2. Validate timeout, retry, rejection, partial fill, disconnect, and reconciliation behavior
3. Explicitly enable a small-capital live account

Safety controls:

- `LIVE_TRADING=false` by default
- Separate paper, testnet, and live credentials/configuration
- Live startup requires both `TRADING_MODE=live` and `LIVE_TRADING=true`
- Per-order, position, exposure, daily-loss, and drawdown limits
- No withdrawal permission
- Client order IDs and a durable order ledger prevent duplicates
- Kill switch and exchange reconciliation before resuming after failure
