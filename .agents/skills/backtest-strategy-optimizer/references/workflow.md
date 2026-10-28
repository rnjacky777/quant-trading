# Workflow and invariants

Run from the repo root using the project virtual environment.

- `python -m scripts.optimize_backtest queue`: find dashboard-marked versions.
- `python -m scripts.optimize_backtest list`: list versions and their experiments.
- `python -m scripts.optimize_backtest analyze-request --request-id ID`: reproduce
  and analyze the marked version's full evidence, without creating a candidate.
- `python -m scripts.optimize_backtest optimize-request --request-id ID`: run the
  deterministic suggested candidate, or record no-change/skipped.
- Add `--changes-json JSON --note REASON` for an agent-proposed hypothesis.
- `analyze --run-key KEY` and `optimize --run-key KEY` remain explicit selection
  paths; they also consider the selected strategy version's other experiments.

Use --db and --exchange before the subcommand when overriding defaults.
strategy_key is the immutable parameter identity; run_key identifies exact
period, data fingerprint, costs and settings. Queue requests are unique per
pending strategy version. They persist referenced run keys, the objective,
changes, reason, candidate link, and per-period base/candidate metrics.

Supported changes:

- Signal: fast, slow, lookback, momentum_threshold, entry_deviation.
- Exit: stop_loss_pct, take_profit_pct (percent units), exit_mode (fixed/signal).
- Risk: risk_per_trade_pct, max_exposure_pct (percent units), leverage (1 only).

Only one group can change per candidate. Reject unsupported or ineffective
changes. Never overwrite parent results. Multiple date tests of the same changed
parameter set share one child version. Repeated/overlapping evidence must not be
counted as independent votes. A failed reproduction stops the request, with an
error, before candidate experiments are created.

Any Validation/OOS result reused in optimization is tuning evidence; preserve its
original label for audit but never call it unseen again. Ordinary dashboard
backtesting is free-form and does not require a locked research plan. Register
new truly unseen periods before claiming generalization.


Stop reentry experiment: `--changes-json '{"stop_reentry_mode":"signal_reset"}'`
changes only exit/reentry policy. A stop blocks new BUY entries until a completed
SELL signal resets the gate; HOLD does not reset it. Take-profit exits are
unaffected. `immediate` preserves the original behavior. Keep other settings
fixed, report skipped winners as well as avoided losses, and never claim that
less turnover guarantees higher net returns.


SMA entry-buffer experiment: `trend_entry_buffer_pct` is a signal-category
change in percent units (1 means 1%). BUY requires fast > slow * (1 + buffer);
SELL remains fast < slow; the interval between is HOLD. It is saved as
`trend_entry_buffer` in fractional units in version policy. Do not sweep buffer
values until an already-viewed losing year becomes profitable. Record failed
alternatives, costs, warmup sensitivity and remaining losses.


Trailing-stop experiment (exit category): pass both `trailing_activation_pct`
and `trailing_distance_pct`, in percent units; both 0 disables the rule.
Only completed closes activate and raise the stop; the update is applied after
all current-bar exits and becomes active next bar. The stop never decreases.
Trailing exits are recorded as `trailing_stop` and obey stop reentry reset.
Initial protective stop, sizing and leverage remain unchanged. Account for gaps
and stop-before-target ambiguity; never claim that a 5%/5% rule ensures breakeven.


Trailing breakout reentry is an exit-policy experiment: set
`trailing_reentry_mode` to `exit_high_breakout` (default `inherit` preserves
old versions). After a trailing exit only, latch the exited candle high.
A later completed close must strictly exceed it and the strategy must issue BUY
before next-bar entry; intrabar highs, equality and HOLD do not qualify.
The existing SELL reset also clears this latch for a new trend.
Original-stop reset and take-profit reentry are unchanged. Never use a future
bar high or the execution bar close to unlock entry. Report both return and
drawdown/cost changes; a higher return alone is not evidence of more stability.
