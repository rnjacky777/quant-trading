---
name: backtest-strategy-optimizer
description: Find dashboard-marked strategy versions, inspect all of their saved backtest evidence, propose one controlled improvement experiment, and save a child candidate with period-by-period comparisons.
---

# Backtest Strategy Optimizer

Follow the project AGENTS.md. Read [references/workflow.md](references/workflow.md).
Use the version-controlled CLI from the project root: `python -m scripts.optimize_backtest`.
The dashboard configures strategies, arbitrary backtest dates, costs, notes and
waiting/cancelled status. AI analysis is performed by the agent, not automatically
by the dashboard or by the deterministic advisor.

## Apply the four-stage optimization cycle

Follow the `AGENTS.md` section **Required optimization cycle: 回測 → 檢討 → 提出優化方式 → 實行並回測** as the canonical workflow:

1. Reproduce the requested baseline and inspect all saved period/cost cases.
2. Review trades, failure conditions, exits, sizing and costs against recorded research lessons.
3. Use AI judgment to propose one evidence-based hypothesis. Consult primary research or original author rules when useful; record sources, access dates, applicability and our implementation differences. Quantify chart patterns causally rather than copying retrospective drawings or claimed returns.
4. Record the proposal before candidate results, implement one category, and rerun the same baseline cases. Save the comparison and decide whether to adopt, retain only as a trade-off, reject, or record insufficient evidence.

The deterministic advisor is an input to analysis, not the AI decision. New candidates do not automatically replace retained baselines. Failed ideas require review and a new justified hypothesis before another experiment; do not sweep nearby parameters until history fits. Separate strategy backtest case counts, code-test counts and candidate counts in reports. A documentation-only workflow update does not authorize running the queue or creating a strategy candidate.

## Select marked work

When asked to optimize or continue marked work, run `queue` first. Work from the
pending strategy version and request ID. Do not select a best-return period or
an unrelated latest version. If there are no marked requests and the intended
version is ambiguous, list versions and ask which to optimize.

## Analyze version evidence

Run `analyze-request --request-id ID`. Inspect all saved results for that exact
strategy_key. The request synchronizes and records evidence run keys before
processing. Reproduce every referenced fingerprint; fail visibly if any period
cannot be reproduced. Never silently omit a losing period. Overlapping periods
and repeated runs are not independent evidence; do not sum their metrics.

Legacy Development/Validation/OOS labels are audit metadata. The user authorizes
using a marked version's results to guide optimization. Record these results as
used-for-tuning evidence; they can no longer support independent unseen claims.
Do not require the user to create a Development branch or a locked date plan
just to test or mark an existing strategy version.

## Propose and save the next candidate

Explain the evidence and one testable hypothesis. The deterministic advisor is
only a starting point. If the AI finds a justified change, execute:

`optimize-request --request-id ID --changes-json JSON --note REASON`

Only one category may change per candidate: signal parameters, exit rules, or
risk sizing. Keep leverage at 1x. The optimizer runs the candidate on every
referenced experiment's same dates, dataset and costs, saves one child strategy
version with its experiments, and records comparisons in the request.

If the default recommendation is appropriate, omit changes-json. If no defensible
change exists, record skipped rather than inventing an improvement. A later
request for the same unchanged proposal must not be described as a new version.
Update pending work to completed, skipped, or failed. Report parent and child,
exact changes, every relevant period comparison, return/risk trade-offs, and
limitations. Do not promote a candidate as proven solely from tuning evidence.
Never change order execution, paper/testnet/live settings, credentials, or keys.

## Judge marked comparisons

The queue also includes `comparison_reviews`, separate from version optimization.
When asked to process comparison judgments, run `analyze-comparison --request-id ID`.
Read the frozen metrics, parameters, data fingerprints, provenance, warnings and
user question, then inspect the referenced saved result snapshots for trades and
curves. Compare return, drawdown, risk-adjusted results, exposure, costs and sample
size. An older version may be preferable; never assume the latest wins or infer
general superiority from one period. Flag unavailable evidence and mismatched
settings. Save a reasoned judgment using `complete-comparison --request-id ID
--summary TEXT`. Do not create a child version from a comparison-review request;
that needs a separately marked optimization task. Follow AGENTS.md for queue scope.


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
