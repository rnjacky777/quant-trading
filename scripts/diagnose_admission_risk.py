"""Replay saved strategies and decompose risk; never alter admission decisions."""
from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.portfolio.research_risk import PortfolioLimits, PortfolioUsage, admission_fraction
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from scripts.research_perpetual_directions import fingerprint
from scripts.research_risk_budget import OUTPUT as SOURCE, late_inputs
from scripts.validate_baseline_2022_2023 import load_inputs

OUTPUT = Path('data/admission-risk-diagnostics.json')


def decompose(event: dict) -> dict:
    """Gross prospective price loss, split at each lot's executed entry."""
    lots = []
    for lot in event['lots']:
        p, c = lot['position'], lot['config']
        q, d, mark = p['quantity'], p['direction'], event['mark']
        stop_fill = p['stop'] * (1 - d * c['slippage_bps'] / 10000)
        price = q * max(d * (mark - stop_fill), 0)
        principal = min(price, q * max(d * (p['entry_price'] - stop_fill), 0))
        costs = q * (stop_fill * c['fee_bps'] / 10000 + mark * c['funding_reserve'])
        lots.append(dict(position_id=lot['position_id'], sleeve=lot['sleeve'], direction=d,
                         remaining_entry_downside=principal, giveback=price-principal, future_costs=costs,
                         unrealized_price_pnl=q*d*(mark-p['entry_price'])))
    total = {k: sum(l[k] for l in lots) for k in ('remaining_entry_downside', 'giveback', 'future_costs')}
    if not isclose(sum(total.values()), event['usage']['open_stop_risk'], abs_tol=1e-7):
        raise ValueError('risk decomposition does not reconcile')
    usage = replace(PortfolioUsage(**event['usage']),
                    open_stop_risk=total['remaining_entry_downside'] + total['future_costs'])
    p = event['proposal']
    fraction, reason = admission_fraction(equity=event['equity'], cash=event['cash'], usage=usage,
        notional=p['quantity'] * max(p['entry_price'], event['mark']),
        margin_and_fee=p['margin']+p['entry_fee'], planned_risk=p['planned_risk'],
        limits=PortfolioLimits(**event['limits']))
    return dict(**total, lots=lots, local_no_giveback_fraction=fraction,
                local_no_giveback_reason=reason, local_only_not_executable=True)


def summarize(events: list[dict]) -> dict:
    blocked = [e for e in events if e['reason']=='open_stop_risk' and e['fraction']<=1e-10]
    partial = [e for e in events if e['reason']=='open_stop_risk' and 1e-10<e['fraction']<1]
    total_risk = sum(e['usage']['open_stop_risk'] for e in blocked)
    return dict(proposals=len(events), blocked=len(blocked), partial=len(partial),
                blocked_groups=dict(Counter(f"{e['sleeve']}/{'long' if e['direction']==1 else 'short'}" for e in blocked)),
                giveback_event_weighted_share=sum(e['decomposition']['giveback'] for e in blocked)/total_risk if total_risk else 0,
                local_unblocked=sum(e['decomposition']['local_no_giveback_fraction']>1e-10 for e in blocked),
                local_partial_increased=sum(e['decomposition']['local_no_giveback_fraction']>e['fraction']+1e-10 for e in partial),
                largest_blocked_risk_fraction=max((e['usage']['open_stop_risk']/e['equity'] for e in blocked), default=0))


def trade_key(t: dict) -> tuple:
    return t['sleeve'], t['direction'], t['entry_timestamp_ms']


def missing_trades(source: dict, row: dict, events: list[dict]) -> dict:
    parent = next(r for r in source['rows'] if r['variant']==source['parent'] and
                  (r['year'],r['fee_bps'],r['slippage_bps'])==(row['year'],row['fee_bps'],row['slippage_bps']))
    current = {trade_key(t) for t in row['result']['trades']}
    event_map = {(e['sleeve'],e['direction'],e['timestamp_ms']): e for e in events}
    missing = []
    for t in parent['result']['trades']:
        if trade_key(t) in current:
            continue
        e = event_map.get(trade_key(t))
        missing.append(dict(trade=t, admission_reason=e['reason'] if e else 'not_observed_proposal',
                            local_no_giveback_fraction=e['decomposition']['local_no_giveback_fraction'] if e else None))
    return dict(count=len(missing), winners=sum(t['trade']['pnl']>0 for t in missing),
                losers=sum(t['trade']['pnl']<0 for t in missing),
                parent_net_pnl=sum(t['trade']['pnl'] for t in missing), trades=missing)


def main() -> None:
    if OUTPUT.exists():
        raise ValueError('diagnostic output exists; do not overwrite evidence')
    source_bytes = SOURCE.read_bytes()
    source = json.loads(source_bytes)
    if source['status']!='completed' or len(source['rows'])!=32:
        raise ValueError('complete 32-case source required')
    early, late = load_inputs(), late_inputs()
    output = dict(status='started', source=str(SOURCE), source_sha256=sha256(source_bytes).hexdigest(),
                  used_for_tuning=True, independent_validation=False, new_candidates=0, rows=[],
                  source_code_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in (
                      'app/backtest/portfolio_research.py', 'app/portfolio/research_risk.py',
                      'scripts/diagnose_admission_risk.py', 'docs/research/2026-10-29-admission-risk-design.md')})
    def save() -> None:
        OUTPUT.write_text(json.dumps(output, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    save()
    try:
        for row in source['rows']:
            year = row['year']
            start = int(datetime(year,1,1,tzinfo=timezone.utc).timestamp()*1000)
            end = int(datetime(year+1,1,1,tzinfo=timezone.utc).timestamp()*1000)
            tape, marks, funding = early[:3] if year<2024 else late
            period = [c for c in tape if start-243*3600000<=c.timestamp_ms<end]
            pm = [m for m in marks if start<=m.timestamp_ms<end]
            rates = [f for f in funding if start<=f.timestamp_ms<end]
            prints = dict(candles=fingerprint([asdict(c) for c in period]), marks=fingerprint([asdict(m) for m in pm]),
                          funding=fingerprint([asdict(f) for f in rates]))
            if prints!=row['input_fingerprints']:
                raise ValueError('saved input fingerprint mismatch')
            strategies = dict(intraday=DirectionalSweepStructureConfirmStrategy(), swing=DirectionalSwingEfficiencyStrategy())
            sleeves = [ResearchSleeve(s['name'], strategies[s['name']], PerpetualResearchConfig(**s['config'])) for s in row['sleeves']]
            events = []
            def observe(event: dict) -> None:
                event['decomposition'] = decompose(event)
                events.append(event)
            result = json.loads(serialize_result(PortfolioResearchEngine(sleeves,
                PortfolioLimits(**source['portfolio_limits']), directional_loss_guard=True, swing_failure_exit=True
            ).run(period, evaluation_start_ms=start, marks=pm, funding=rates, admission_observer=observe)))
            if result!=row['result']:
                raise ValueError('observed replay changed full saved result')
            record = dict(year=year,variant=row['variant'],fee_bps=row['fee_bps'],slippage_bps=row['slippage_bps'],
                          reproduction='full_snapshot_equal',input_fingerprints=prints,metrics=result['metrics'],
                          summary=summarize(events), events=events,
                          all_admission_counts=dict(Counter(a['status']+'/'+a['reason'] for a in result['admissions'])))
            if row['variant']==source['candidate']:
                record['missing_parent_trades']=missing_trades(source,row,events)
            output['rows'].append(record)
            save()
            print(row['variant'],year,row['fee_bps'],row['slippage_bps'],record['summary'],flush=True)
        output.update(status='completed', strategy_replays=32)
        save()
    except Exception as exc:
        output.update(status='failed',error=str(exc))
        save()
        raise


if __name__=='__main__':
    main()
