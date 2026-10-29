# Objective A risk-budget results

2026-10-29. One candidate; 32 strategy backtest cases; 46 relevant code tests passed (including four new evidence-audit cases).

Parent: portfolio_swing_failure_exit. Child: portfolio_risk_budget_055. Only both sleeves risk_per_trade changes 0.25% → 0.55%.
Each year resets to 10,000 USDT. Actual funding, completed 4h context, next-hour execution, 243h warmup. All 2022–2025 evidence is used for tuning.

Decision: **reject_objective_a_solution**. Original baseline retained; no automatic promotion.

## Full period comparisons

|Year|Fee/slippage bps|Parent net %|Child net %|Parent DD %|Child DD %|Trades parent/child|Lost parent winners|
|---|---|---:|---:|---:|---:|---|---:|
|2022|5/5|-0.112|0.722|-2.316|-4.718|52/45|2|
|2022|10/5|-0.314|0.226|-2.384|-4.790|52/45|2|
|2022|10/10|-0.500|-0.239|-2.447|-4.858|52/45|2|
|2022|20/10|-0.892|-1.089|-2.562|-4.984|52/45|2|
|2023|5/5|5.047|7.182|-1.742|-2.998|33/31|2|
|2023|10/5|4.578|6.545|-1.763|-3.097|33/31|2|
|2023|10/10|4.150|5.948|-1.783|-3.201|33/31|2|
|2023|20/10|2.640|4.858|-1.819|-3.382|35/31|2|
|2024|5/5|4.798|9.375|-2.148|-3.911|59/51|5|
|2024|10/5|4.149|6.934|-2.192|-3.746|59/53|4|
|2024|10/10|3.555|5.743|-2.251|-3.785|59/53|4|
|2024|20/10|2.475|3.669|-2.471|-3.856|60/53|4|
|2025|5/5|-0.136|-0.084|-2.385|-4.841|58/54|2|
|2025|10/5|-0.572|-0.855|-2.517|-5.110|59/54|2|
|2025|10/10|-0.817|-1.539|-2.643|-5.359|59/54|1|
|2025|20/10|-1.516|-2.791|-2.879|-5.834|59/54|1|

## Objective gates

```json
{
  "portfolio_swing_failure_exit": {
    "mean_annual_returns": {
      "5/5": 0.023993340794963236,
      "10/5": 0.019601474941266794,
      "10/10": 0.01597009538228994,
      "20/10": 0.006767504758280585
    },
    "worst_annual_return_all_costs": -0.015159626828935902,
    "worst_drawdown_all_costs": -0.02879256212101089,
    "passed": false
  },
  "portfolio_risk_budget_055": {
    "mean_annual_returns": {
      "5/5": 0.042989178501731035,
      "10/5": 0.03212427212105576,
      "10/10": 0.02478005422122745,
      "20/10": 0.011618749025971792
    },
    "worst_annual_return_all_costs": -0.027912476630871597,
    "worst_drawdown_all_costs": -0.058339125224677546,
    "passed": false
  }
}
```

Arithmetic annual averages are not a continuous-account CAGR. Bounds apply to every year/cost case. Doubled primary cost is 10/10; legacy 20/10 is also retained.

## Metrics for every version and case

Exposure is fraction of bars invested, not average gross notional. Funding is signed cash flow; fees/slippage and average win/loss are USDT.

|Version|Year|Cost|CAGR %|Sharpe|Sortino|Win %|PF|Avg win|Avg loss|Exposure %|Fees|Slippage|Funding|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|parent|2022|5/5|-0.112|-0.029|-0.040|28.846|0.976|29.768|-12.371|21.196|26.272|26.272|-1.557|
|parent|2022|10/5|-0.315|-0.106|-0.150|28.846|0.932|28.855|-12.548|21.196|50.970|25.485|-1.505|
|parent|2022|10/10|-0.501|-0.180|-0.254|28.846|0.893|27.987|-12.699|21.196|49.475|49.475|-1.454|
|parent|2022|20/10|-0.893|-0.354|-0.498|26.923|0.813|27.677|-12.544|21.196|91.886|45.943|-1.535|
|parent|2023|5/5|5.051|1.643|2.800|33.333|3.099|67.743|-10.930|19.450|23.319|23.319|-16.302|
|parent|2023|10/5|4.582|1.560|2.650|33.333|2.873|63.840|-11.109|19.450|44.656|22.328|-15.599|
|parent|2023|10/10|4.153|1.478|2.501|33.333|2.673|60.284|-11.276|19.450|42.844|42.845|-14.955|
|parent|2023|20/10|2.642|1.057|1.744|31.429|1.979|48.505|-11.232|19.450|77.349|38.675|-12.288|
|parent|2024|5/5|4.788|1.549|2.294|38.983|1.971|42.352|-13.731|23.301|45.784|45.784|-38.279|
|parent|2024|10/5|4.140|1.393|2.055|38.983|1.827|39.841|-13.930|23.301|87.605|43.803|-37.041|
|parent|2024|10/10|3.547|1.239|1.821|38.983|1.700|37.539|-14.109|23.301|83.980|83.980|-35.886|
|parent|2024|20/10|2.470|0.925|1.350|38.333|1.476|33.355|-14.045|23.301|154.967|77.484|-33.697|
|parent|2025|5/5|-0.136|-0.048|-0.069|32.759|0.971|23.925|-12.003|19.804|42.723|42.723|-7.136|
|parent|2025|10/5|-0.572|-0.251|-0.361|32.203|0.880|22.003|-11.882|19.804|81.341|40.671|-6.822|
|parent|2025|10/10|-0.817|-0.387|-0.554|30.508|0.825|21.417|-11.395|19.804|75.312|75.312|-6.121|
|parent|2025|20/10|-1.517|-0.788|-1.114|28.814|0.685|19.369|-11.449|19.804|136.571|68.286|-5.571|
|child|2022|5/5|0.723|0.179|0.256|28.889|1.086|69.811|-26.103|20.831|50.144|50.144|-3.593|
|child|2022|10/5|0.226|0.073|0.103|28.889|1.027|66.636|-26.365|20.831|96.868|48.434|-3.496|
|child|2022|10/10|-0.240|-0.033|-0.046|28.889|0.972|63.663|-26.611|20.831|93.706|93.706|-3.403|
|child|2022|20/10|-1.090|-0.239|-0.336|26.667|0.874|63.177|-26.273|20.831|176.067|88.034|-3.230|
|child|2023|5/5|7.187|1.541|2.606|29.032|2.347|139.059|-24.243|18.993|46.155|46.155|-20.973|
|child|2023|10/5|6.550|1.446|2.437|29.032|2.208|132.950|-24.637|18.993|88.667|44.334|-20.448|
|child|2023|10/10|5.952|1.351|2.269|29.032|2.081|127.203|-25.002|18.993|85.304|85.304|-19.933|
|child|2023|20/10|4.862|1.165|1.943|29.032|1.861|116.698|-25.656|18.993|158.597|79.299|-18.945|
|child|2024|5/5|9.355|1.714|2.547|35.294|1.944|107.278|-30.106|21.559|91.840|91.841|-60.136|
|child|2024|10/5|6.919|1.434|2.117|35.849|1.694|89.094|-29.394|21.559|172.276|86.138|-54.670|
|child|2024|10/10|5.731|1.238|1.817|35.849|1.569|83.355|-29.690|21.559|164.161|164.162|-52.678|
|child|2024|20/10|3.662|0.856|1.241|35.849|1.357|73.387|-30.218|21.559|300.505|150.253|-49.141|
|child|2025|5/5|-0.084|-0.001|-0.001|31.481|0.991|52.197|-24.208|19.279|80.892|80.892|-10.818|
|child|2025|10/5|-0.856|-0.201|-0.293|31.481|0.906|48.766|-24.717|19.279|155.115|77.557|-10.538|
|child|2025|10/10|-1.540|-0.389|-0.563|31.481|0.834|45.616|-25.119|19.279|148.640|148.640|-10.266|
|child|2025|20/10|-2.793|-0.763|-1.091|29.630|0.709|42.466|-25.226|19.279|270.490|135.245|-9.559|

## Primary-cost attribution and frequency

|Version|Year|Group|Trades|Net USDT|
|---|---|---|---:|---:|
|portfolio_swing_failure_exit|2022|swing/short|29|135.87|
|portfolio_swing_failure_exit|2022|intraday/short|10|-59.37|
|portfolio_swing_failure_exit|2022|swing/long|9|-73.05|
|portfolio_swing_failure_exit|2022|intraday/long|4|-14.66|
|portfolio_swing_failure_exit|2023|swing/long|16|517.03|
|portfolio_swing_failure_exit|2023|intraday/long|2|15.40|
|portfolio_swing_failure_exit|2023|swing/short|14|-17.55|
|portfolio_swing_failure_exit|2023|intraday/short|1|-10.16|
|portfolio_swing_failure_exit|2024|swing/long|33|451.39|
|portfolio_swing_failure_exit|2024|swing/short|8|-89.91|
|portfolio_swing_failure_exit|2024|intraday/long|12|191.66|
|portfolio_swing_failure_exit|2024|intraday/short|6|-73.36|
|portfolio_swing_failure_exit|2025|swing/long|23|-15.84|
|portfolio_swing_failure_exit|2025|intraday/long|5|-37.55|
|portfolio_swing_failure_exit|2025|swing/short|19|-52.71|
|portfolio_swing_failure_exit|2025|intraday/short|11|92.55|
|portfolio_risk_budget_055|2022|swing/short|23|348.27|
|portfolio_risk_budget_055|2022|intraday/short|10|-133.51|
|portfolio_risk_budget_055|2022|swing/long|8|-108.85|
|portfolio_risk_budget_055|2022|intraday/long|4|-33.66|
|portfolio_risk_budget_055|2023|swing/long|14|746.19|
|portfolio_risk_budget_055|2023|intraday/long|2|34.13|
|portfolio_risk_budget_055|2023|swing/short|14|-39.57|
|portfolio_risk_budget_055|2023|intraday/short|1|-22.57|
|portfolio_risk_budget_055|2024|swing/long|25|883.40|
|portfolio_risk_budget_055|2024|swing/short|8|-200.56|
|portfolio_risk_budget_055|2024|intraday/long|12|422.62|
|portfolio_risk_budget_055|2024|intraday/short|6|-167.96|
|portfolio_risk_budget_055|2025|swing/long|21|7.21|
|portfolio_risk_budget_055|2025|intraday/long|5|-81.90|
|portfolio_risk_budget_055|2025|swing/short|17|-103.80|
|portfolio_risk_budget_055|2025|intraday/short|11|170.12|

|Version|Year|Entries|UTC active days|Entries/calendar day|Entries/active day|Max leverage|Max gross %|Drift bars|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|portfolio_swing_failure_exit|2022|52|45|0.142|1.156|1|21.345|238|
|portfolio_swing_failure_exit|2023|33|29|0.090|1.138|1|26.960|537|
|portfolio_swing_failure_exit|2024|59|49|0.161|1.204|1|27.273|580|
|portfolio_swing_failure_exit|2025|58|49|0.159|1.184|1|27.607|241|
|portfolio_risk_budget_055|2022|45|39|0.123|1.154|1|35.536|622|
|portfolio_risk_budget_055|2023|31|27|0.085|1.148|1|33.540|687|
|portfolio_risk_budget_055|2024|51|44|0.139|1.159|1|44.842|815|
|portfolio_risk_budget_055|2025|54|47|0.148|1.149|1|46.244|616|

## Interpretation

Primary-cost mean rises from 2.399% to 4.299%, below 5%; doubled-cost mean is 2.478%. Worst stress year is -2.791%, worst drawdown 5.834%. Reject as an Objective A solution, retaining the original baseline.
The 2.2x budget is not a 2.2x return. Primary-cost stop-risk rejected admissions increase 6→14, 8→10, 11→19 and 4→8 for 2022–2025. Trades fall 52→45, 33→31, 59→51 and 58→54. Lost parent winners number 2/2/5/2, representing parent PnL 37.12/41.27/106.63/3.20 USDT; these amounts are diagnostics, not recoverable profit forecasts.
Matched trades have identical exit timestamps in all four primary-cost years. Shared/directional final loss-brake multipliers change for four matched 2024 trades, and none in the other three years. Results therefore combine larger quantities, admission selection and path-dependent brakes; no causal claim that a specific new filter improved edge.
The primary-cost candidate has negative months in 7/7/5/6 months across 2022–2025. Its largest positive months include June 2022 (+3.69%), January 2023 (+4.31%) and February 2024 (+5.40%); 2025 March is -2.79%. Monthly snapshots reveal concentrated returns, not stable daily income.
Maximum primary-cost stop-risk fraction reaches 5.97% after entry, although the admission cap stays 1%. The engine measures potential loss from current mark to fixed stops, including unrealized gains that could be given back. This is a material limitation of interpreting the cap as a continuous risk ceiling. Actual leverage remains 1x, and primary-cost gross exposure peaks below 50%.
Next diagnostic, not another authorized experiment: inspect blocked entries and separate initial-capital loss from giveback of unrealized profits before considering any change to aggregate stop-risk admission. Do not simply raise limits or sweep the per-trade budget.

## Reproduction and limitations

- Ten pre-existing baseline full snapshots reproduced exactly; two primary-cost 2024/2025 cases reproduced saved metrics (original full snapshots were not saved). All twelve fingerprints matched. Four 10/10 parent cases are new cost experiments.
- Post-run audit of all 32 cases confirmed every accepted admission respects gross, stop-risk and collateral budgets; all 16 candidate configs differ only in risk_per_trade and all actual trades use 1x. These checks do not make admission limits continuous holding limits.
- Full trades, equity curves, monthly mark-to-market returns, admissions and loss-brake traces for all 32 cases are in data/perpetual-risk-budget-055.json. Parent artifacts and one-shot validation registry were not modified.
- No entry/exit implementation changed. Existing causal-timing tests pass; this does not prove the absence of all bias. Fixed BTC universe avoids ex-post asset selection within this experiment but cannot establish multi-asset generality. Four viewed years provide no independent validation.
- Fixed slippage does not simulate order-book depth, market impact, latency distributions or historical exchange margin brackets. Missing historical funding marks use the previously documented same-hour mark open. Research lots do not establish exchange hedge-mode support.
- Exposure and stop-risk limits govern admissions; subsequent price movement can exceed them. Drift bars are explicitly reported. No forced rebalancing or new liquidation rule was introduced.
- One candidate only. Do not sweep nearby budgets following failure. Any further candidate requires a new evidence-based hypothesis. Forward paper evidence is still required; paper/testnet gates remain.
