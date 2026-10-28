"""Replay the user-selected baseline and save diagnostics without tuning it."""
from collections import Counter, defaultdict
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.frequency import entry_frequency
from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.path_diagnostics import completed_close_path, monthly_equity
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from scripts.research_perpetual_directions import fingerprint


def main() -> None:
    source = Path('data/perpetual-swing-failure-exit.json')
    root = Path('data/btc-perpetual-1h')
    tape = [Candle('binance-usdm', 'BTC/USDT', '1h', int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')])
        for r in json.loads((root/'klines.json').read_text())]
    marks = [MarkPriceCandle('binance-usdm','BTC/USDT',int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close')],timeframe='1h')
        for r in json.loads((root/'markPriceKlines.json').read_text())]
    funding = [FundingRate('binance-usdm','BTC/USDT',int(r['fundingTime']),
        float(r['fundingRate']),float(r['markPrice']))
        for r in json.loads((root/'funding-api.json').read_text())]
    parents = json.loads(source.read_text())['rows']
    if len(parents) != 4 or {(r['year'],r['cost_multiplier']) for r in parents} != {(2024,1),(2024,2),(2025,1),(2025,2)}:
        raise ValueError('Four unique baseline cases required')
    cases = []
    for parent in parents:
        if parent['variant'] != 'portfolio_swing_failure_exit' or parent['status'] != 'completed':
            raise ValueError('Wrong or incomplete baseline')
        year = parent['year']
        start, end = (1704067200000,1735689600000) if year == 2024 else (1735689600000,1767225600000)
        period = [c for c in tape if start-243*3600000 <= c.timestamp_ms < end]
        pm = [m for m in marks if start <= m.timestamp_ms < end]
        rates = [f for f in funding if start <= f.timestamp_ms < end]
        if [c.timestamp_ms for c in period] != list(range(start-243*3600000,end,3600000)):
            raise ValueError('Incomplete candle timeline')
        fp = dict(candles=fingerprint([asdict(c) for c in period]),
            marks=fingerprint([asdict(m) for m in pm]),funding=fingerprint([asdict(f) for f in rates]))
        if fp != parent['input_fingerprints']:
            raise ValueError('Input fingerprint mismatch')
        strategies = dict(intraday=DirectionalSweepStructureConfirmStrategy(),swing=DirectionalSwingEfficiencyStrategy())
        if any(s['strategy'] != strategies[s['name']].name for s in parent['sleeves']):
            raise ValueError('Strategy identity mismatch')
        sleeves = [ResearchSleeve(s['name'],strategies[s['name']],PerpetualResearchConfig(**s['config'])) for s in parent['sleeves']]
        events = []
        result = PortfolioResearchEngine(sleeves,PortfolioLimits(**parent['portfolio_limits']),
            directional_loss_guard=parent['directional_loss_guard'],swing_failure_exit=parent['swing_failure_exit']).run(
                period,evaluation_start_ms=start,marks=pm,funding=rates,signal_observer=events.append)
        snapshot = json.loads(serialize_result(result))
        if snapshot != parent['result']:
            raise ValueError('Full baseline snapshot mismatch')
        trades = snapshot['trades']
        groups = defaultdict(lambda: dict(count=0,pnl=0.,fees=0.,funding=0.))
        paths = []
        for t in trades:
            for label in (f"{t['sleeve']}/{t['direction']}",f"{t['sleeve']}/exit/{t['exit_reason']}"):
                g = groups[label]
                g['count'] += 1
                for key in ('pnl','fees','funding'):
                    g[key] += t[key]
            paths.append(dict(position_id=t['position_id'],sleeve=t['sleeve'],direction=t['direction'],
                pnl=t['pnl'],**completed_close_path(t,period)))
        daily = Counter(t['entry_timestamp_ms']//86400000 for t in trades)
        if max(daily.values(),default=0) > 2 or any(t['leverage'] != 1 for t in trades):
            raise ValueError('Daily cap or realized leverage differs from expected baseline')
        case = dict(year=year,cost=parent['cost_multiplier'],full_snapshot_equal=True,input_fingerprints=fp,
            metrics=snapshot['metrics'],settings={k:parent[k] for k in ('sleeves','portfolio_limits','directional_loss_guard','swing_failure_exit')},
            frequency=entry_frequency(trades,year),groups=dict(groups),monthly_equity=monthly_equity(snapshot,year),
            completed_close_paths=paths,signal_outcomes=dict(Counter(e['outcome']['status'] for e in events)),
            signals=events,maximum_concurrent_positions=result.maximum_concurrent_positions)
        cases.append(case)
        print(json.dumps({k:case[k] for k in ('year','cost','full_snapshot_equal','metrics','frequency','groups','signal_outcomes')},ensure_ascii=False),flush=True)
    sources = [source,root/'klines.json',root/'markPriceKlines.json',root/'funding-api.json',Path(__file__)]
    sources += list(Path('app/backtest').glob('*.py')) + list(Path('app/strategies').glob('*.py')) + list(Path('app/portfolio').glob('*.py'))
    Path('data/swing-failure-baseline-review.json').write_text(json.dumps(dict(
        status='completed_review',baseline='portfolio_swing_failure_exit',used_for_tuning=True,
        independent_validation=False,new_candidate=None,cases=cases,
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2,allow_nan=False),encoding='utf-8')


if __name__ == '__main__':
    main()
