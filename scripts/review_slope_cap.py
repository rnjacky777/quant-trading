"""Recompute causal sizing evidence and retain all cost/period trade-offs."""
from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import replace
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.frequency import entry_frequency
from app.backtest.long_short_research import LongShortResearchEngine, PerpetualResearchConfig
from app.data.models import Candle
from app.risk.regime import directional_slope_cap
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy


def main() -> None:
    parent_path=Path('data/perpetual-swing-failure-exit.json');child_path=Path('data/perpetual-slope-risk-cap.json')
    parent_payload=json.loads(parent_path.read_text());payload=json.loads(child_path.read_text())
    parents={(r['year'],r['cost_multiplier']):r for r in parent_payload['rows']}
    rows=payload['rows']
    assert payload['category']=='risk' and payload['parent']=='portfolio_swing_failure_exit'
    assert len(rows)==4 and {(r['year'],r['cost_multiplier']) for r in rows}=={(2024,1),(2024,2),(2025,1),(2025,2)}
    tape_path=Path('data/btc-perpetual-1h/klines.json')
    tape=[Candle('binance-usdm','BTC/USDT','1h',int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[]
    for row in rows:
        key=(row['year'],row['cost_multiplier']);parent=parents[key]
        assert row['status']==parent['status']=='completed' and row['slope_risk_cap']
        for field in ('config','portfolio_limits','sleeves','input_fingerprints','intraday_exit_rule','directional_loss_guard','swing_failure_exit'):
            assert row[field]==parent[field],field
        start=1704067200000 if row['year']==2024 else 1735689600000
        warmup=bisect_left(times,start-243*3600000)
        result=row['result'];trades=result['trades'];admissions=[a for a in result['admissions'] if a['status']=='accepted']
        assert len({t['position_id'] for t in trades})==len(trades)==len(admissions)
        by_id={t['position_id']:t for t in trades}
        assert isclose(result['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        assert all(t['leverage']==1 for t in trades)
        for a in admissions:
            t=by_id[a['position_id']];i=bisect_left(times,t['entry_timestamp_ms']);history=tape[warmup:i]
            strategy=DirectionalSwingEfficiencyStrategy() if t['sleeve']=='swing' else DirectionalSweepStructureConfirmStrategy()
            signal=strategy.generate(history)
            assert signal.direction==t['direction'] and isclose(signal.stop_loss_price,t['stop_loss_price'],abs_tol=1e-7)
            trace=a['slope_risk_trace'];loss=a['loss_guard_trace']
            cap=directional_slope_cap(history,t['direction'])
            assert trace['slope_cap']==cap
            assert trace['loss_brake']==loss['final_brake_multiplier']==min(loss['shared_multiplier'],loss['directional_multiplier'])
            multiplier=min(trace['loss_brake'],cap)
            assert trace['capped_multiplier']==trace['sizing_multiplier']==loss['sizing_multiplier']==multiplier
            config=PerpetualResearchConfig(**next(s['config'] for s in row['sleeves'] if s['name']==t['sleeve']))
            config=replace(config,max_exposure=min(config.max_exposure,row['portfolio_limits']['max_gross_exposure']))
            _,proposal=LongShortResearchEngine(config)._open(a['equity_before'],tape[i],signal,multiplier)
            assert proposal is not None
            assert isclose(proposal.quantity*a['scale'],a['quantity'],abs_tol=1e-10)
            assert isclose(proposal.planned_risk*a['scale'],a['planned_risk'],abs_tol=1e-7)
            eq=a['equity_before'];limits=row['portfolio_limits']
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
        pevents={(t['sleeve'],t['direction'],t['entry_timestamp_ms']):t for t in parent['result']['trades']}
        cevents={(t['sleeve'],t['direction'],t['entry_timestamp_ms']):t for t in trades}
        same_paths=pevents.keys()==cevents.keys();resized=[]
        for k,t in cevents.items():
            p=pevents.get(k)
            if not p:continue
            same=all(t[f]==p[f] for f in ('entry_price','exit_price','exit_timestamp_ms','exit_reason','stop_loss_price'))
            same_paths=bool(same_paths and same)
            if not isclose(t['quantity'],p['quantity'],abs_tol=1e-10):
                resized.append(dict(sleeve=t['sleeve'],direction=t['direction'],entry_ms=t['entry_timestamp_ms'],
                    parent_pnl=p['pnl'],child_pnl=t['pnl'],parent_quantity=p['quantity'],child_quantity=t['quantity'],
                    slope_cap=next(a['slope_risk_trace']['slope_cap'] for a in admissions if a['position_id']==t['position_id'])))
        groups=defaultdict(lambda:dict(count=0,pnl=0.))
        for t in trades:
            g=groups[f"{t['sleeve']}/{t['direction']}"];g['count']+=1;g['pnl']+=t['pnl']
        cases.append(dict(year=key[0],cost=key[1],checks='passed',parent_metrics=parent['result']['metrics'],metrics=result['metrics'],
            frequency=entry_frequency(trades,key[0]),same_entry_exit_price_paths=same_paths,grouped=dict(groups),
            resized_trades=resized,reduced_parent_winners=[t for t in resized if t['parent_pnl']>0 and t['child_quantity']<t['parent_quantity']]))
    lines=['# 慢均線方向衝突風險上限：全年比較','',
        '父portfolio_swing_failure_exit → portfolio_slope_risk_cap；只改風控：完成4h SMA60的24h斜率不支持方向時，risk multiplier=min(原連虧倍率,0.5)。保持訊號／stop／波段失效退出、每日2新單與1x。事前設計見2026-10-28-slope-cap-design.md。',
        '每年10,000 USDT，單邊fee/slippage一般10/5bps、雙成本20/10bps，含實際funding與mark。四筆父完整快照及資料指紋一致才跑候選。全部2024/2025都是調參證據。','',
        '|年|成本|父收益|候選收益|父DD|候選DD|總筆數|短線筆數|',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for c in cases:
        p,m=c['parent_metrics'],c['metrics'];f=c['frequency']
        lines.append(f"|{c['year']}|{c['cost']}|{p['total_return']:+.3%}|{m['total_return']:+.3%}|{p['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{m['number_of_trades']}|{f['intraday']}|")
    all_return=all(c['metrics']['total_return']>c['parent_metrics']['total_return'] for c in cases)
    all_dd=all(c['metrics']['maximum_drawdown']>=c['parent_metrics']['maximum_drawdown'] for c in cases)
    lines+=['',f'四組收益全改善：{all_return}；四組回撤皆不退步：{all_dd}。',
        '判斷：保留風控取捨候選，不宣稱全面升級；2025仍虧，10%目標未達，短線18/16筆頻率未改善。收益提升若來自倉位配置，不等於找到新訊號優勢。',
        '原贏家也可能被縮倉；下方逐筆列出。共享cash與連虧路徑導致後續部位數量變化，即使entry/exit不變也不應直接相減舊交易PnL。',
        '250項pytest通過，另逐筆重算完成bar cap、原signal/stop、risk/stop/cost推導quantity、共享gross/stoprisk/margin、daily2與cash/PnL。原MMR2%非歷史級距、1h OHLC路徑、深度/precision/min quantity、虛擬lot映射限制保留。無paper/testnet/live升級。']
    for c in cases:lines+=['',f"## {c['year']}／成本{c['cost']}倍完整指標與取捨",'','```json',json.dumps(c,ensure_ascii=False,indent=2),'```']
    Path('docs/research/2026-10-28-slope-cap-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=[parent_path,child_path,tape_path,Path(__file__),Path('scripts/research_slope_cap.py'),Path('scripts/research_portfolio_overlap.py'),
        Path('app/backtest/portfolio_research.py'),Path('app/risk/regime.py'),Path('data/btc-perpetual-1h/markPriceKlines.json'),Path('data/btc-perpetual-1h/funding-api.json')]
    Path('data/slope-cap-audit.json').write_text(json.dumps(dict(status='completed_research_candidate',independent_validation=False,
        all_return_improved=all_return,all_drawdown_not_worse=all_dd,source_sha256={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},cases=cases),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(all_return_improved=all_return,all_drawdown_not_worse=all_dd,
        cases=[dict(year=c['year'],cost=c['cost'],return_pct=c['metrics']['total_return']*100,dd_pct=c['metrics']['maximum_drawdown']*100,same_paths=c['same_entry_exit_price_paths']) for c in cases]),indent=2))


if __name__=='__main__':
    main()
