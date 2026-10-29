# Objective A: one risk-budget candidate

2026-10-29. User selected A before this experiment. All 2022–2025 data are now tuning evidence for this candidate; the original one-shot validation record remains untouched.

Objective: arithmetic mean of four calendar-year net returns >=5%, each year reset to 10,000 USDT; absolute maximum drawdown <=10% in each year; worst annual net return >=-3%. Primary costs 5/5 bps fee/slippage; doubled costs 10/10 bps must have positive four-year arithmetic mean. Drawdown and worst-year limits must also hold in stress cases. Preserve legacy 10/5 and 20/10 cases. Four years x four costs x two versions =32 strategy cases, one candidate.

Observed problem: baseline primary-cost mean is 2.399334%, with annual returns -0.112002%, +5.047167%, +4.797717%, -0.135547%. Linear target multiplier is 2.083912, only a feasibility estimate. Hypothesis: increasing per-trade risk from 0.0025 to 0.0055 (2.2x, rounded up to the next 0.05 percentage-point risk increment) can increase average return enough while retaining risk headroom. No nearby sweeps if it fails.

Parent portfolio_swing_failure_exit; child portfolio_risk_budget_055. Change risk_per_trade only for both sleeves. Keep entry/exit rules, loss brakes, daily two-entry cap, 50% gross exposure, 1% aggregate stop-risk and 50% margin admission limits. Keep maximum_leverage config unchanged (2); report actual leverage, do not claim the config is 1. Funding/mark inputs and 243-hour warmup unchanged. Exposure caps, compound sizing, loss brakes and admission competition make linear projections unreliable. Negative years may worsen. This differs from prior selective direction/slope risk caps: one uniform budget increase, no signal-dependent filter.

Reproduce all 12 saved baseline cases before candidate runs (full snapshots where saved; metrics for 2024/2025 5/5 cases whose full snapshots were not saved). Add four 10/10 baseline cases. Fail on fingerprint or reproduction mismatch. Save separate full snapshots, monthly equity, direction/sleeve attribution, admission constraints, winners lost, and frequency. No automatic baseline promotion. No live orders or exchange hedge-mode claim; historical margin brackets remain unverified.

Decision thresholds fixed before results: retain only as a trade-off candidate if all Objective A gates pass; otherwise reject as an Objective A solution, retaining the original baseline. Future evidence requires forward paper observation, followed by testnet before live. Short-horizon frequency remains secondary; no forced trades.
