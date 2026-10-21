---
name: backtest-strategy-optimizer
description: Select a saved quant backtest version, diagnose its evidence, run one controlled optimization experiment, and save the result as a child strategy version. Use for requests to improve, optimize, branch, or create the next version from an existing backtest result.
---

# Backtest Strategy Optimizer

Work from the `quant-trading` project root. Use
`scripts/optimize_backtest.py` for deterministic version lookup, reproduction,
analysis, and persistence. Read [references/workflow.md](references/workflow.md)
before creating a new version.

## Select the base

- When the user refers to Dashboard-marked results, run `queue`, select the
  intended request, and use `optimize-request --request-id <id>`.
- If the user supplied a version or run key, resolve that exact result.
- If selection is ambiguous, run `list` and ask which result to use. Do not
  silently select the highest-return result.
- Treat `strategy_key` as the stable strategy identifier and `run_key` as the
  exact experiment identifier. Version numbers are scoped to symbol, timeframe,
  and strategy family. Select the Development `run_key` whose evidence should
  drive the optimization.

## Analyze before changing

Run `analyze` and report the evidence, recommendation, and validation plan.
Do not manufacture a parameter change when the advisor reports insufficient
trades or recommends validation. Optimization is allowed only for a
Development result. Never tune a Validation or Out-of-Sample result.

## Create the child version

When a controlled candidate exists and the request authorizes optimization,
run `optimize` with the selected Development `run_key` and a concise hypothesis. The script
reproduces the base dataset, changes only the recommended fields, runs the
candidate, and saves it with `base_run_key`. A new version is created only when
the strategy or risk parameters change; dates, stages, data, cash, fees, and
slippage remain experiment properties.

Report both base and candidate metrics. A saved candidate is an experiment,
not a promoted strategy. Do not describe it as improved unless the relevant
Development metrics improve and a separate Validation run supports the claim.
Never alter paper, testnet, live trading, API keys, or order execution through
this skill.
