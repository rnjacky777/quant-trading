"""One preregistered risk-only experiment on already-seen 2022–2025 data."""
from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.data.models import Candle, MarkPriceCandle, FundingRate
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from scripts.research_perpetual_directions import fingerprint
from scripts.validate_baseline_2022_2023 import load_inputs, attribution, SOURCES

OUTPUT = Path('data/perpetual-risk-budget-055.json')
DESIGN = Path('docs/research/2026-10-29-risk-budget-design.md')
COSTS = ((5, 5), (10, 5), (10, 10), (20, 10))


def read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def late_inputs() -> tuple[list[Candle], list[MarkPriceCandle], list[FundingRate]]:
    root = Path('data/btc-perpetual-1h')
    tape = [Candle('binance-usdm', 'BTC/USDT', '1h', int(r['open_time']),
                   *[float(r[k]) for k in ('open', 'high', 'low', 'close', 'volume')])
            for r in read(str(root / 'klines.json'))]
    marks = [MarkPriceCandle('binance-usdm', 'BTC/USDT', int(r['open_time']),
                            *[float(r[k]) for k in ('open', 'high', 'low', 'close')], timeframe='1h')
             for r in read(str(root / 'markPriceKlines.json'))]
    funding = [FundingRate('binance-usdm', 'BTC/USDT', int(r['fundingTime']),
                           float(r['fundingRate']), float(r['markPrice']))
               for r in read(str(root / 'funding-api.json'))]
    return tape, marks, funding


def diagnostics(result: dict, year: int) -> dict:
    trades = result['trades']
    days = Counter(t['entry_timestamp_ms'] // 86400000 for t in trades)
    if max(days.values(), default=0) > 2:
        raise ValueError('daily entry cap violated')
    months = {}
    for p in result['portfolio_curve']:
        month = datetime.fromtimestamp(p['timestamp_ms'] / 1000, timezone.utc).strftime('%Y-%m')
        months[month] = p['equity']
    previous = 10000.
    monthly = {}
    for month, equity in months.items():
        monthly[month] = dict(equity=equity, return_pct=equity / previous - 1)
        previous = equity
    curve = result['portfolio_curve']
    return dict(attribution=attribution(trades), monthly_mark_to_market=monthly,
                entries=len(trades), active_utc_days=len(days),
                entries_per_calendar_day=len(trades) / (366 if year == 2024 else 365),
                entries_per_active_day=len(trades) / len(days) if days else 0,
                maximum_entries_per_day=max(days.values(), default=0),
                actual_max_leverage=max((t['leverage'] for t in trades), default=0),
                maximum_concurrent_positions=result['maximum_concurrent_positions'],
                maximum_gross_fraction=max(p['gross_exposure'] / p['equity'] for p in curve),
                maximum_stop_risk_fraction=max(p['open_stop_risk'] / p['equity'] for p in curve),
                admission_limit_drift_bars=sum(p['admission_limit_exceeded'] for p in curve),
                admissions=dict(Counter(a['status'] + '/' + a['reason'] for a in result['admissions'])))


def objective(rows: list[dict], variant: str) -> dict:
    selected = [r for r in rows if r['variant'] == variant]
    means = {f'{fee}/{slip}': sum(r['result']['metrics']['total_return'] for r in selected
             if (r['fee_bps'], r['slippage_bps']) == (fee, slip)) / 4 for fee, slip in COSTS}
    worst = min(r['result']['metrics']['total_return'] for r in selected)
    drawdown = min(r['result']['metrics']['maximum_drawdown'] for r in selected)
    return dict(mean_annual_returns=means, worst_annual_return_all_costs=worst,
                worst_drawdown_all_costs=drawdown,
                passed=means['5/5'] >= .05 and means['10/10'] > 0 and worst >= -.03 and drawdown >= -.10)


def main() -> None:
    if OUTPUT.exists():
        raise ValueError('Output exists; never overwrite experiment evidence')
    parents = read('data/perpetual-swing-failure-exit.json')['rows']
    early_saved = read('data/validation-2022-2023-baseline.json')['rows']
    fees_saved = read('data/verified-fee-baseline.json')['rows']
    template = next(r for r in parents if r['cost_multiplier'] == 1)
    early = load_inputs()
    late = late_inputs()
    sources = (*SOURCES, 'scripts/research_risk_budget.py', str(DESIGN))
    artifact = dict(schema='risk_budget_objective_a_v1', parent='portfolio_swing_failure_exit',
                    candidate='portfolio_risk_budget_055', category='risk', used_for_tuning=True,
                    independent_validation=False, status='started', rows=[],
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in sources},
                    historical_margin_brackets_verified=False, funding_mark_fills=early[3],
                    design=str(DESIGN), portfolio_limits=template['portfolio_limits'])
    def save() -> None:
        OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    save()
    try:
        for variant, risk in (('portfolio_swing_failure_exit', .0025), ('portfolio_risk_budget_055', .0055)):
            for year in range(2022, 2026):
                start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
                end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
                tape, marks, funding = early[:3] if year < 2024 else late
                period = [c for c in tape if start - 243 * 3600000 <= c.timestamp_ms < end]
                pm = [m for m in marks if start <= m.timestamp_ms < end]
                rates = [f for f in funding if start <= f.timestamp_ms < end]
                prints = dict(candles=fingerprint([asdict(c) for c in period]),
                              marks=fingerprint([asdict(m) for m in pm]), funding=fingerprint([asdict(f) for f in rates]))
                for fee, slip in COSTS:
                    strategies = dict(intraday=DirectionalSweepStructureConfirmStrategy(), swing=DirectionalSwingEfficiencyStrategy())
                    sleeves = [ResearchSleeve(s['name'], strategies[s['name']], replace(
                        PerpetualResearchConfig(**s['config']), risk_per_trade=risk, fee_bps=fee, slippage_bps=slip))
                        for s in template['sleeves']]
                    result = json.loads(serialize_result(PortfolioResearchEngine(sleeves,
                        PortfolioLimits(**template['portfolio_limits']), directional_loss_guard=True,
                        swing_failure_exit=True).run(period, evaluation_start_ms=start, marks=pm, funding=rates)))
                    reproduction = 'new_cost_case'
                    if risk == .0025 and (fee, slip) != (10, 10):
                        if year < 2024:
                            old = next(r for r in early_saved if r['year'] == year and r['fee_bps'] == fee)
                        elif fee == 5:
                            old = next(r for r in fees_saved if r['year'] == year)
                        else:
                            old = next(r for r in parents if r['year'] == year and r['cost_multiplier'] == fee / 10)
                        if prints != old['input_fingerprints']:
                            raise ValueError(f'{year}/{fee}: input fingerprint changed')
                        if 'result' in old:
                            if result != old['result']:
                                raise ValueError(f'{year}/{fee}: full snapshot changed')
                            reproduction = 'full_snapshot_equal'
                        else:
                            if result['metrics'] != old['metrics']:
                                raise ValueError(f'{year}/{fee}: saved metrics changed')
                            reproduction = 'metrics_equal_only_full_snapshot_not_previously_saved'
                    row = dict(year=year, variant=variant, fee_bps=fee, slippage_bps=slip,
                               input_fingerprints=prints, sleeves=[dict(name=s.name, strategy=s.strategy.name,
                               config=asdict(s.config)) for s in sleeves], result=result,
                               diagnostics=diagnostics(result, year), reproduction=reproduction)
                    if risk != .0025:
                        parent = next(r for r in artifact['rows'] if r['variant'] == artifact['parent'] and
                                      (r['year'], r['fee_bps'], r['slippage_bps']) == (year, fee, slip))
                        if parent['input_fingerprints'] != prints:
                            raise ValueError('candidate input mismatch')
                        row['parent_metrics'] = parent['result']['metrics']
                        def key(t: dict) -> tuple:
                            return t['sleeve'], t['direction'], t['entry_timestamp_ms']
                        child_trades = {key(t): t for t in result['trades']}
                        row['lost_parent_winners'] = [t for t in parent['result']['trades']
                            if t['pnl'] > 0 and (key(t) not in child_trades or child_trades[key(t)]['pnl'] <= 0)]
                    artifact['rows'].append(row)
                    save()
                    m = result['metrics']
                    print(variant, year, fee, slip, f"return={m['total_return']:.6%} dd={m['maximum_drawdown']:.6%}", reproduction, flush=True)
        artifact['objectives'] = {v: objective(artifact['rows'], v) for v in (artifact['parent'], artifact['candidate'])}
        artifact['decision'] = 'keep_tradeoff_candidate' if artifact['objectives'][artifact['candidate']]['passed'] else 'reject_objective_a_solution'
        artifact['status'] = 'completed'
        save()
        print(json.dumps(artifact['objectives'], indent=2), flush=True)
    except Exception as exc:
        artifact.update(status='failed', error=str(exc))
        save()
        raise


if __name__ == '__main__':
    main()
