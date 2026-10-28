# Research plan registered 2026-10-22

All boundaries are UTC; ends are exclusive. This plan is recorded before the
risk-budget candidate is evaluated. It does not restore unseen status to history.

## Question and fixed candidate

Does replacing all-cash allocation with a 0.5% per-trade planned loss budget
reduce drawdown at an acceptable cost in return? This is a risk-control
experiment, not evidence that entry signals improve.

- Base: BTC/USDT spot, 4h, SMA 20/60, 5% protective stop, 10% target, 1x leverage.
- Base experiment: `d2c17eae00e745cfedc0caf590eca3616f6dc8f6b74a5e8e271771897341369e`.
- Candidate: change sizing only; 0.5% equity risk per trade, including modeled
  entry/exit costs. Exposure ceiling stays 100%, leverage stays 1x.
- Keep initial cash 10,000 USDT, fee 10 bps, slippage 5 bps on each side.
- Percentage stops remain relative to the entry fill, identical to V1.
- Do not also change the exit mode in V2. Signal-only targets are a later,
  separate experiment; protective stops remain active in either mode.

## Periods

| Role | Start | End | Interpretation |
|---|---|---|---|
| Development | 2020-03-01 | 2023-01-01 | Already observed; includes rising and falling BTC regimes |
| Retrospective validation | 2023-01-01 | 2026-09-30 | Already observed; stability comparison only |
| Reserved holdout | 2026-10-23 | 2027-04-23 | Future prices; cannot evaluate until complete |

The original full-period run and overlapping Validation runs have already been
viewed. They are not independent out-of-sample evidence. No tuning is allowed
against the validation or holdout results. Future market regimes cannot be
guaranteed in advance. A future historical holdout is not forward paper trading.

Full-period V1/V2 comparisons over 2020-03-01 to 2026-09-30 are exploratory.
Compare the fixed versions again over the registered development and
retrospective validation windows; each run resets capital and uses only past
candles for warm-up. Annual attribution within a run preserves positions.

## Evaluation and limits

Report all required performance metrics, trade count, cost, exit reasons and
annual returns. Accept the sizing control functionally only if ordinary stop
fills respect planned budgets and exposure/cash caps. For research, report the
drawdown/return trade-off without choosing a winner by total return alone. Do
not promote the candidate for paper/live based solely on these seen periods.

BTC/ETH correlations, liquidity/market-impact calibration, portfolio-wide risk,
drawdown/daily-loss/consecutive-loss circuit breakers, and forward paper
execution remain future gates. Gap fills may exceed a planned stop budget.
