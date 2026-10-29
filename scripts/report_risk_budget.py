"""Render the saved, complete Objective A experiment without rerunning it."""
import json
from pathlib import Path

from scripts.research_risk_budget import OUTPUT


def main() -> None:
    data = json.loads(OUTPUT.read_text(encoding='utf-8'))
    if data['status'] != 'completed' or len(data['rows']) != 32:
        raise ValueError('all 32 cases must complete before reporting')
    rows = data['rows']
    text = ['# Objective A risk-budget results', '', '2026-10-29. One candidate; 32 strategy backtest cases; 46 relevant code tests passed (including four new evidence-audit cases).',
            '', 'Parent: portfolio_swing_failure_exit. Child: portfolio_risk_budget_055. Only both sleeves risk_per_trade changes 0.25% → 0.55%.',
            'Each year resets to 10,000 USDT. Actual funding, completed 4h context, next-hour execution, 243h warmup. All 2022–2025 evidence is used for tuning.',
            '', f"Decision: **{data['decision']}**. Original baseline retained; no automatic promotion.", '',
            '## Full period comparisons', '', '|Year|Fee/slippage bps|Parent net %|Child net %|Parent DD %|Child DD %|Trades parent/child|Lost parent winners|',
            '|---|---|---:|---:|---:|---:|---|---:|']
    for row in rows:
        if row['variant'] != data['candidate']:
            continue
        p, c = row['parent_metrics'], row['result']['metrics']
        text.append(f"|{row['year']}|{row['fee_bps']}/{row['slippage_bps']}|{p['total_return']*100:.3f}|{c['total_return']*100:.3f}|{p['maximum_drawdown']*100:.3f}|{c['maximum_drawdown']*100:.3f}|{p['number_of_trades']}/{c['number_of_trades']}|{len(row['lost_parent_winners'])}|")
    text += ['', '## Objective gates', '', '```json', json.dumps(data['objectives'], indent=2), '```', '',
             'Arithmetic annual averages are not a continuous-account CAGR. Bounds apply to every year/cost case. Doubled primary cost is 10/10; legacy 20/10 is also retained.', '',
             '## Metrics for every version and case', '',
             'Exposure is fraction of bars invested, not average gross notional. Funding is signed cash flow; fees/slippage and average win/loss are USDT.', '',
             '|Version|Year|Cost|CAGR %|Sharpe|Sortino|Win %|PF|Avg win|Avg loss|Exposure %|Fees|Slippage|Funding|',
             '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        m = row['result']['metrics']
        values = [m['cagr']*100, m['sharpe_ratio'], m['sortino_ratio'], m['win_rate']*100,
                  m['profit_factor'], m['average_win'], m['average_loss'], m['exposure']*100,
                  m['fees'], m['slippage'], m['net_funding']]
        text.append(f"|{'parent' if row['variant']==data['parent'] else 'child'}|{row['year']}|{row['fee_bps']}/{row['slippage_bps']}|" + '|'.join(f'{v:.3f}' for v in values) + '|')
    text += ['', '## Primary-cost attribution and frequency', '',
             '|Version|Year|Group|Trades|Net USDT|', '|---|---|---|---:|---:|']
    for row in rows:
        if (row['fee_bps'], row['slippage_bps']) != (5, 5):
            continue
        for group, value in row['diagnostics']['attribution'].items():
            text.append(f"|{row['variant']}|{row['year']}|{group}|{value['trades']}|{value['net_pnl']:.2f}|")
    text += ['', '|Version|Year|Entries|UTC active days|Entries/calendar day|Entries/active day|Max leverage|Max gross %|Drift bars|',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        if (row['fee_bps'], row['slippage_bps']) == (5, 5):
            d = row['diagnostics']
            text.append(f"|{row['variant']}|{row['year']}|{d['entries']}|{d['active_utc_days']}|{d['entries_per_calendar_day']:.3f}|{d['entries_per_active_day']:.3f}|{d['actual_max_leverage']}|{d['maximum_gross_fraction']*100:.3f}|{d['admission_limit_drift_bars']}|")
    text += ['', '## Interpretation', '',
             'Primary-cost mean rises from 2.399% to 4.299%, below 5%; doubled-cost mean is 2.478%. Worst stress year is -2.791%, worst drawdown 5.834%. Reject as an Objective A solution, retaining the original baseline.',
             'The 2.2x budget is not a 2.2x return. Primary-cost stop-risk rejected admissions increase 6→14, 8→10, 11→19 and 4→8 for 2022–2025. Trades fall 52→45, 33→31, 59→51 and 58→54. Lost parent winners number 2/2/5/2, representing parent PnL 37.12/41.27/106.63/3.20 USDT; these amounts are diagnostics, not recoverable profit forecasts.',
             'Matched trades have identical exit timestamps in all four primary-cost years. Shared/directional final loss-brake multipliers change for four matched 2024 trades, and none in the other three years. Results therefore combine larger quantities, admission selection and path-dependent brakes; no causal claim that a specific new filter improved edge.',
             'The primary-cost candidate has negative months in 7/7/5/6 months across 2022–2025. Its largest positive months include June 2022 (+3.69%), January 2023 (+4.31%) and February 2024 (+5.40%); 2025 March is -2.79%. Monthly snapshots reveal concentrated returns, not stable daily income.',
             'Maximum primary-cost stop-risk fraction reaches 5.97% after entry, although the admission cap stays 1%. The engine measures potential loss from current mark to fixed stops, including unrealized gains that could be given back. This is a material limitation of interpreting the cap as a continuous risk ceiling. Actual leverage remains 1x, and primary-cost gross exposure peaks below 50%.',
             'Next diagnostic, not another authorized experiment: inspect blocked entries and separate initial-capital loss from giveback of unrealized profits before considering any change to aggregate stop-risk admission. Do not simply raise limits or sweep the per-trade budget.',
             '', '## Reproduction and limitations', '',
             '- Ten pre-existing baseline full snapshots reproduced exactly; two primary-cost 2024/2025 cases reproduced saved metrics (original full snapshots were not saved). All twelve fingerprints matched. Four 10/10 parent cases are new cost experiments.',
             '- Post-run audit of all 32 cases confirmed every accepted admission respects gross, stop-risk and collateral budgets; all 16 candidate configs differ only in risk_per_trade and all actual trades use 1x. These checks do not make admission limits continuous holding limits.',
             '- Full trades, equity curves, monthly mark-to-market returns, admissions and loss-brake traces for all 32 cases are in data/perpetual-risk-budget-055.json. Parent artifacts and one-shot validation registry were not modified.',
             '- No entry/exit implementation changed. Existing causal-timing tests pass; this does not prove the absence of all bias. Fixed BTC universe avoids ex-post asset selection within this experiment but cannot establish multi-asset generality. Four viewed years provide no independent validation.',
             '- Fixed slippage does not simulate order-book depth, market impact, latency distributions or historical exchange margin brackets. Missing historical funding marks use the previously documented same-hour mark open. Research lots do not establish exchange hedge-mode support.',
             '- Exposure and stop-risk limits govern admissions; subsequent price movement can exceed them. Drift bars are explicitly reported. No forced rebalancing or new liquidation rule was introduced.',
             '- One candidate only. Do not sweep nearby budgets following failure. Any further candidate requires a new evidence-based hypothesis. Forward paper evidence is still required; paper/testnet gates remain.']
    Path('docs/research/2026-10-29-risk-budget-results.md').write_text('\n'.join(text) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
