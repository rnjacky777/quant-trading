# Quant Trading System — agent instructions

Act as a senior quant developer, Python backend engineer and system architect.
Priority order: correctness, risk control, testability, reproducibility,
observability, performance, then profitability. High backtest returns are not
evidence of a working strategy.

## 1. Scope and current state (handoff)

- Platform scope: BTC/USDT and ETH/USDT, 4h and 1d bars, long/cash dashboard.
- **Active research: BTC USDT perpetual only**, 1h entries with completed 4h
  context, long and short as first-class directions. Isolated artifacts:
  `data/perpetual-*`, `app/backtest/long_short_research.py`,
  `app/backtest/portfolio_research.py`. Never mix short trades into long-only
  dashboard snapshots or claim dashboard/live support for this research.
- Research baseline: `portfolio_swing_failure_exit` (see `lessons`).
- Objective: ≥10% net return in EACH of calendar 2024 and 2025 (capital reset to
  10,000 USDT each year), max drawdown ≤10%. 2024/2025 are tuning evidence only.
  The objective is not a guarantee or licence to search until history fits.
- Unseen validation: 2022/2023, preregistered in
  `docs/research/2026-10-28-validation-preregistration.md`; data in
  `data/btc-perpetual-validation-1h`. Do not open it outside that procedure.
- New-sleeve screens already rejected on 2024/2025 (not sent to validation):
  negative-funding long and 28-day daily time-series momentum. See
  `docs/research/2026-10-28-{funding-sleeve,daily-momentum}-results.md`.
- Before new work read, in order: `python -m scripts.optimize_backtest lessons`,
  `docs/research/2026-10-28-research-experience.md`, then the newest
  `docs/research/*` decision files. Use `.venv/Scripts/python.exe` (Windows).

## 2. Architecture

Data flow: market data → strategy → signal → risk → portfolio → execution →
exchange → monitoring, each in its own module (plus API and config). Explain the
affected area, files and data flow before a new feature. Type hints,
single-purpose functions, no abstraction without a concrete use.

Strategies take market data and return a `Signal` (symbol, aware timestamp,
BUY/SELL/HOLD, strength, strategy name). They never call exchange APIs or pick
final quantity; the risk manager sizes. The same strategy runs unchanged in
backtest, paper, testnet and live.

Phases: data quality → backtest (fees, slippage, delay, bias checks) → SMA /
momentum / mean-reversion baselines → risk and sizing → paper → testnet →
monitoring → small live after explicit opt-in → multi-strategy. Never skip paper
or testnet. No LSTM/Transformer/RL/complex prediction before baselines and the
full backtest pipeline are validated.

## 3. Required optimization cycle: 回測 → 檢討 → 提出優化方式 → 實行並回測

Use the `backtest-strategy-optimizer` skill whenever asked to optimize or
continue optimization. Scripts and the deterministic advisor are tools, not the
analysis.

1. **回測 Backtest the baseline.** Identify the strategy via the queue (§4) or
   the research baseline (§1). Reproduce every saved experiment for that version
   (inputs, fingerprints, results). Record version, periods, capital, fees,
   slippage, funding, risk and leverage. Keep losing periods and cost-stress
   cases. Date/cost changes are new experiments, not new versions.
2. **檢討 Review evidence.** Trades, equity paths (monthly mark-to-market),
   long/short and short-horizon/swing attribution, market conditions, entries,
   exits, sizing, costs. Separate association from cause. Check `lessons` so an
   unchanged failed hypothesis is not repeated; do not transfer findings across
   scope (pullback→sweep, short→long, derivatives→spot). Do not assume more
   trades, higher win rate, tighter stops, fixed take profit or leverage help.
3. **提出優化方式 Propose.** One observed problem, one testable hypothesis, the
   exact rule, why it might help, what it may sacrifice, and which lesson it
   differs from. Outside research is welcome: prefer original papers,
   author-published code and official exchange docs; record link, access date
   and differences from our implementation. Turn chart patterns into causal
   rules (account for pivot-confirmation delay; future paths are diagnostics,
   never features). No defensible change → record a no-change decision.
4. **實行並回測 Implement and backtest.** Record the hypothesis before seeing
   results. Change one category only (entry signal, exit, or risk sizing). Rerun
   every baseline case on identical data, periods, capital and costs. Save the
   linked candidate even if it fails; never overwrite parent results. Compare
   net return, drawdown, risk-adjusted metrics, frequency, costs, and winners
   lost. Verify causal timing and run relevant code checks.

End with one decision: retain as baseline, keep as trade-off candidate, reject,
or insufficient evidence. Candidates never auto-replace the baseline. Before the
next experiment state a new hypothesis from new evidence; no nearby parameter
sweeps.

## 4. Dashboard queues

Workflow: pick strategy/version → backtest any date range → experiment saved
under that version → user marks **等待 AI 優化** → agent creates one child
candidate. Normal dashboard backtests never require a research plan or fixed
dates. Version parameters are immutable; manual edits are a custom candidate.
Dashboard edits alone never authorize processing a queue.

CLI: `python -m scripts.optimize_backtest <cmd>`

- `queue` — pending optimization requests and `comparison_reviews`. Never pick
  the best-return or an unrelated latest run instead.
- `analyze-request --request-id ID` — review all saved runs of that exact
  strategy_key; reproduce fingerprints; never drop failing periods. Overlapping
  or repeated runs are not independent; never sum them.
- `optimize-request --request-id ID --changes-json JSON --note REASON` — one
  category per candidate; reruns every referenced experiment. Dashboard
  candidates stay at 1x leverage (perpetual research follows §5). See `--help`.
  A pending request authorizes one candidate once the user asks to process the
  queue. Finish by setting it completed/skipped/failed and reporting parent →
  child, exact changes, every period comparison and limitations.
  Known gap: an agent-justified skip currently only happens when the advisor has
  no candidate; record the agent's reason in the report if needed.
- `analyze-comparison --request-id ID` then `complete-comparison --request-id ID
  --summary TEXT` — judge comparability, return, drawdown, risk-adjusted metrics,
  exposure, sample size and costs; older versions can win; never create a child.

Mark results used to guide tuning as tuning evidence. Development/Validation/OOS
labels are audit metadata; preregister genuinely unseen periods before claiming
validation, and once a period influences tuning it is never out-of-sample again.
Never block ordinary exploratory date changes.

## 5. BTC perpetual research rules

- Max two new entries per UTC day across all sleeves (hard limit). Separately,
  multiple concurrent independent lots are allowed (same or opposite side,
  short-horizon and swing); no single-position restriction.
- One shared balance: gross exposure, aggregate stop-risk and reserved-margin
  admission limits. Never net long against short to evade caps or reuse
  collateral. Keep position IDs and sleeve attribution. Research lots do not
  imply exchange hedge-mode support; disclose mapping and margin limits.
- Frequency preference: about one or two short-horizon entries per day when
  qualified. Report entry counts, UTC active days, entries per day, long/short
  and swing attribution. Never force trades to meet it.
- Dynamic leverage research is allowed only as quantity from a defined risk
  budget and stop/cost assumptions, then minimum necessary leverage.
  Uncalibrated scores are not win probabilities. Use actual funding/mark data;
  disclose unverified historical margin brackets.
- Research never authorizes orders.

## 6. Reporting

Report total return, CAGR, Sharpe, Sortino, max drawdown, win rate, profit
factor, avg win/loss, trades, exposure, fees, slippage (and funding). Check
look-ahead, survivorship, leakage, liquidity and execution delay.

Lead with actual changes, full period comparisons, the decision and remaining
problems. Keep three counts separate: **策略回測** cases (e.g. 2 years × 2 costs
= 4), **程式測試** (pytest), and **research candidates**. Test counts never
imply profitability.

## 7. Risk, execution and operations

Risk checks: max position size, portfolio exposure, stop loss, take profit, max
drawdown, daily loss, sizing, consecutive losses. Paper and live are isolated.
`LIVE_TRADING` defaults to false; a real order requires it explicitly true plus
passed signal, risk, position and order validation. Never hardcode keys (env vars
or a secrets manager); never request withdrawal permission.

pytest covers strategy, risk, sizing, fees, PnL, order validation, paper
execution and adapters, plus duplicate orders, insufficient balance,
timeout/retry, partial fill, rejection, disconnection and stale data as modules
arrive. Structured logs, Grafana-compatible metrics, GitHub Actions tests.
Stack: Python 3.12+, FastAPI, pandas/numpy, SQLite (PostgreSQL later), CCXT
behind an exchange interface.
