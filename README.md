# Quant Trading System

BTC derivatives research experience: read
`python -m scripts.optimize_backtest lessons` before proposing another candidate.
The [evidence-linked experience ledger](docs/research/2026-10-28-research-experience.md)
records twenty controlled experiments, including failed and mixed outcomes. Rebuild
the ledger and [monthly/path diagnosis](docs/research/2026-10-28-monthly-path-review.md)
with `python -m scripts.research_experience`. These are tuning observations, not
independent validation or automatic trading instructions.

For complete baseline signal diagnostics (including risk/quota rejections and
open-exit suppression), run `python -m scripts.research_all_signals` and read
[the all-signal report](docs/research/2026-10-28-all-signal-results.md).
This replays all four saved baseline snapshots unchanged. Its 4/12/24-hour
cost-adjusted event observations are not executable portfolio returns and must
not be summed into annual performance.

The project implements historical closed-candle ingestion, reproducible baseline
backtests, a research dashboard, and initial risk-budget sizing. It has no order
submission code or exchange credentials.

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
SMA periods, stop loss, take profit, sizing policy, exposure cap, or exit mode. Changing dates, research stage,
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

## Additional baseline strategies

The CLI also accepts `--strategy momentum --lookback 20 --momentum-threshold 0.02`
and `--strategy mean-reversion --lookback 20 --entry-deviation 0.05`, with the
same symbol, timeframe, since, and until arguments shown above. Thresholds are
fractions: `0.02` means 2%. Momentum buys when the return over the lookback
exceeds its threshold and exits otherwise. Mean reversion buys at or below 5%
under the trailing mean, exits at or above the mean, and holds between those
levels. The mean includes the latest completed candle. Both strategies load
pre-period warm-up data and execute on the following candle's open through the
existing engine. They are available in both the CLI and dashboard. These are
uncalibrated research baselines, not validated trading
strategies. Record research periods before comparing or tuning them.

## Risk sizing and strategy exits

The dashboard defaults to a 0.5% per-trade equity risk budget and 1x leverage.
The CLI opts in with `--risk-per-trade-pct 0.5 --stop-loss-pct 5`. Strategy
signals carry the protective percentage rule; the risk module sets quantity
from loss to the stop, including modeled round-trip costs. Quantity is also
capped by cash and `--max-exposure-pct` (default 100). Setting risk to zero
replays legacy allocation; it does not mean zero risk. Gaps can exceed planned
loss. The cap currently covers a single-market backtest, not a BTC/ETH portfolio.

`--exit-mode fixed` retains a fixed target plus signal exits and protective
stops. `--exit-mode signal` ignores the fixed target, retaining signal exits
and protective stops: SMA/momentum exit on SELL, mean reversion at the mean.
Buy-and-hold has no SELL and therefore exits only by protection or end-of-data
in signal mode. Percentage stops are the baseline; ATR/support stops remain
future work. Research UI and CLI are fixed at 1x; legacy engine tests remain
available for accounting reproduction.

CLI backtests now save experiments and return run/strategy IDs. All sizing and
exit settings participate in version identity and are preserved on replay.
The optimizer entry point is `python -m scripts.optimize_backtest`; the local
skill delegates to that versioned implementation.

## Dashboard and AI optimization

The main dashboard is free-form: select strategy family and immutable version,
choose any available date range, and run. Every result is saved under that
version. Changing dates, cash or costs does not create a strategy version.
Selecting a saved version locks its signal/risk settings while preserving your
dates. Use "新策略／自訂參數" only to create a manual candidate.

Each version expands to its saved periods and results. Set an objective and
click "標記等待 AI 優化"; cancel a pending request in the same dashboard.
Marking does not invoke an AI API. Ask the repo agent to process the queue.
The agent follows AGENTS.md, uses `queue` → `analyze-request` →
`optimize-request`, and considers every saved backtest for the marked version.
Requests synchronize evidence before processing and record source run IDs,
changes, reasons, child version and per-period comparisons. Duplicate pending
marks of the same version reuse the request. The agent can supply a justified
`--changes-json` proposal instead of relying on deterministic advisor rules.

Historical validation labels are retained for audit. Results reused in
optimization are explicitly tuning evidence and cannot support independent
unseen claims. The optional legacy research-plan API/CLI remains available
for strict preregistration, but it is not required in the dashboard workflow.
CLI examples are `--research-plan-id ID --stage validation`.
Ends are exclusive. Explicit out-of-sample evaluation requires a plan;
holdout dates must not overlap any saved experiment, across markets/timeframes.
The first successful saved holdout consumes it atomically. An exploratory run
over reserved dates also makes them ineligible as unseen data. Existing labels
are retained for audit; previously viewed history remains retrospective.

Annual result tables attribute the continuous equity curve without resetting
positions. [The registered plan](docs/research-plan-2026-10-22.md) and
[V1/V2 review](docs/backtests/2026-10-22-risk-budget-review.md) document the
current experiment and its limitations.

## Compare saved backtests

The primary comparison flow starts at `/backtests/select` ("回測比較" in the
navigation): select market/timeframe and **one** saved date interval. A single
list shows all experiments for every strategy version in that exact interval.
Check any two records (for example V1 and V3), then compare PnL, metrics and
saved equity curves. The list includes capital/cost settings and direct result
links. Changing the interval clears selection; browsing never executes or
creates a backtest. There are no A/B interval selectors.

Click "查看結果" beside any experiment to open its saved equity curve, metrics,
annual attribution and trade ledger without rerunning the engine or creating a
new experiment. This is also available from each comparison card. The permalink
is `GET /backtests/results/RUN_KEY`.

Select two checkboxes in the dashboard's backtest history or a version's
backtest page, then click "比較兩筆回測". Selection persists across those pages
within the browser tab. The comparison shows net PnL, all baseline metrics,
and overlaid equity curves on a shared actual-time axis and value scale.
Switch to an initial-100 index when comparing relative performance. Different
periods, markets, cash, costs, risk settings and data fingerprints are flagged;
they are not silently aligned or treated as a controlled strategy comparison.

New experiments atomically save full result snapshots in SQLite's
`backtest_results`: performance metrics, trades and every equity point.
Snapshots are immutable and do not create another strategy version. Duplicate
runs retain the first snapshot. Saved comparisons remain available even if the
underlying market dataset is later updated or deleted. Legacy runs without a
snapshot are reproduced only if their original candle fingerprint and saved
metrics match, then cached with a "reproduced" source label. If exact recovery
fails, comparison retains the original summary and explains why its curve is
unavailable. The endpoint is `GET /backtests/compare?run_keys=A&run_keys=B`.

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
