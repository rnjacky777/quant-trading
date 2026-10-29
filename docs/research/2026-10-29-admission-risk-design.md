# Admission-risk decomposition: diagnostic plan

2026-10-29. User requested the next diagnostic following the risk-budget experiment. No new strategy candidate or parameter search is part of this diagnostic.

Replay all 32 saved cases in perpetual-risk-budget-055.json (two versions, four years, four cost pairs). Compare input fingerprints and the entire serialized result exactly. A new optional observer receives a deep copy of the book, proposal and usage at the actual admission point, after opening exits and before admission, respecting sleeve order. It neither chooses trades nor changes sizing. Daily-cap and invalid-entry rejections occur before this observer and are counted from saved admissions separately.

For each open lot, using executed entry E, current mark M, direction d, quantity q and slipped stop S:

- mark-to-stop price risk = q max(d(M-S),0).
- remaining entry-to-stop downside = min(mark-to-stop price risk, q max(d(E-S),0)). This is remaining prospective price downside, not original risk and not cash already lost.
- unrealized-profit giveback = mark-to-stop price risk minus remaining entry-to-stop downside.
- future costs = q (S fee + M funding_reserve). Entry fees and funding already paid are sunk and remain in cash/equity; do not add them again.

These three nonnegative components must sum to the existing portfolio open_stop_risk. Long and short lots sum gross, never offset. Costs and funding assumptions are unchanged. This decomposition handles marks between entry and stop without falsely counting already-incurred price loss as future loss.

Diagnostic only: calculate the admission fraction if only the giveback component were excluded from existing-lot risk, with the same equity, proposal, gross and collateral limits. Call it a local counterfactual, never an executable trade or return. Preserve every rejected/partial event and full-budget counts. Show blocked-event composition by year/cost/version and sleeve/direction. Match baseline executed trades absent from the 0.55% version, reporting winners AND losers; do not extrapolate saved PnL to different quantities or sum overlapping cost experiments.

Review feasibility against the 0.701082 percentage-point mean-return gap (280.43 USDT total across four separately funded years) and 20/10 worst-year -2.791% proximity to -3%. Removing giveback from admission risk permits more loss from current equity, directly relevant to Objective A drawdown. No new rule merely because it admits past winners. End with no-change / insufficient-evidence decision unless a separately documented causal hypothesis is warranted; do not change the retained baseline.
