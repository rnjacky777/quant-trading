# Workflow and invariants

## Commands

Run from the project root with the project virtual environment:

```powershell
.\.venv\Scripts\python.exe .agents\skills\backtest-strategy-optimizer\scripts\optimize_backtest.py list
.\.venv\Scripts\python.exe .agents\skills\backtest-strategy-optimizer\scripts\optimize_backtest.py analyze --run-key <64-char-run-key>
.\.venv\Scripts\python.exe .agents\skills\backtest-strategy-optimizer\scripts\optimize_backtest.py optimize --run-key <64-char-run-key> --note "hypothesis"
.\.venv\Scripts\python.exe .agents\skills\backtest-strategy-optimizer\scripts\optimize_backtest.py queue
.\.venv\Scripts\python.exe .agents\skills\backtest-strategy-optimizer\scripts\optimize_backtest.py optimize-request --request-id <id>
```

Use `--db` when `QUANT_DB_PATH` does not point to the intended SQLite file.
Use `--exchange` only when the candle dataset is stored under another exchange
identifier.

## Interpretation

- `list` returns version-scoped identifiers and aggregate metrics.
- `queue` returns versions marked in the Dashboard; `optimize-request` writes
  the outcome back to the optimization log page.
- `analyze` reproduces the selected run from its exact candle fingerprint and
  returns one recommendation or a reason to stop.
- `optimize` refuses non-Development versions and missing or changed datasets.
- `optimize` saves at most one controlled candidate per invocation. Identical
  settings reuse the existing run rather than creating a duplicate version.
- `previous_run_key` preserves the selected parent even when it is not the
  latest version.

## Review

Compare total return, maximum drawdown, Sharpe, Profit Factor, trade count,
fees, and exposure. Prefer lower risk and stability across Validation over the
largest Development return. If the candidate is worse, retain it as negative
research evidence and do not promote it.
