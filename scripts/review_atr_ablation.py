"""All-period review of removing only the inherited hourly ATR entry floor."""
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
from app.strategies.sweep_no_atr_floor import DirectionalSweepNoAtrFloorStrategy
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from app.strategies.swing_failure import breakout_boundary, breakout_failed


def main() -> None:
    ppath=Path('data/perpetual-swing-failure-exit.json');cpath=Path('data/perpetual-atr-ablation.json')
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(ppath.read_text())['rows']}
    payload=json.loads(cpath.read_text());rows=payload['rows'];assert payload['category']=='signal'
    assert len(rows)==4 and {(r['year'],r['cost_multiplier']) for r in rows}=={(2024,1),(2024,2),(2025,1),(2025,2)}
    tpath=Path('data/btc-perpetual-1h/klines.json')
    tape=[Candle('binance-usdm','BTC/USDT','1h',int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tpath.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[]
    for r in rows:
        key=(r['year'],r['cost_multiplier']);p=parents[key]
        assert r['status']==p['status']=='completed'
        for field in ('config','portfolio_limits','input_fingerprints','intraday_exit_rule','directional_loss_guard','swing_failure_exit'):
            assert r[field]==p[field],field
        assert 'slope_risk_cap' not in r
        for a,b in zip(r['sleeves'],p['sleeves'],strict=True):
            assert a['config']==b['config'] and a['name']==b['name']
            assert a['strategy']==b['strategy'] if a['name']=='swing' else a['strategy']==DirectionalSweepNoAtrFloorStrategy.name
        result=r['result'];trades=result['trades'];aa={a['position_id']:a for a in result['admissions'] if a['status']=='accepted'}
        assert len(aa)==len(trades)==len({t['position_id'] for t in trades})
        assert isclose(result['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert all(t['leverage']==1 for t in trades)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        start=1704067200000 if key[0]==2024 else 1735689600000;warm=bisect_left(times,start-243*3600000)
        added=[]
        for t in trades:
            a=aa[t['position_id']];i=bisect_left(times,t['entry_timestamp_ms']);j=bisect_left(times,t['exit_timestamp_ms']);hist=tape[warm:i]
            strategy=DirectionalSwingEfficiencyStrategy() if t['sleeve']=='swing' else DirectionalSweepNoAtrFloorStrategy()
            signal=strategy.generate(hist)
            assert signal.direction==t['direction'] and isclose(signal.stop_loss_price,t['stop_loss_price'],abs_tol=1e-7)
            config=PerpetualResearchConfig(**next(s['config'] for s in r['sleeves'] if s['name']==t['sleeve']))
            config=replace(config,max_exposure=min(config.max_exposure,r['portfolio_limits']['max_gross_exposure']))
            trace=a['loss_guard_trace'];multiplier=min(trace['shared_multiplier'],trace['directional_multiplier'])
            assert multiplier==trace['final_brake_multiplier']==trace['sizing_multiplier']
            _,proposal=LongShortResearchEngine(config)._open(a['equity_before'],tape[i],signal,multiplier)
            assert proposal is not None
            assert isclose(a['quantity'],proposal.quantity*a['scale'],abs_tol=1e-10)
            assert isclose(a['planned_risk'],proposal.planned_risk*a['scale'],abs_tol=1e-7)
            eq=a['equity_before'];limits=r['portfolio_limits']
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
            if t['sleeve']=='swing':
                boundary=breakout_boundary(hist,t['direction']);assert a['breakout_level']==boundary
                eligible=[k for k in range(i+1,j+1) if breakout_failed(tape[warm:k],t['direction'],boundary)]
                assert not eligible or eligible[0]==j
                if t['exit_reason']=='breakout_failure':assert eligible
            elif DirectionalSweepStructureConfirmStrategy().generate(hist).direction==0:
                added.append(dict(position_id=t['position_id'],direction=t['direction'],entry_ms=t['entry_timestamp_ms'],
                    pnl=t['pnl'],fees=t['fees'],funding=t['funding'],exit_reason=t['exit_reason']))
        def event(t):return t['sleeve'],t['direction'],t['entry_timestamp_ms']
        actual={event(t) for t in trades}
        missing=[dict(position_id=t['position_id'],pnl=t['pnl'],sleeve=t['sleeve'],direction=t['direction']) for t in p['result']['trades'] if event(t) not in actual]
        groups=defaultdict(lambda:dict(count=0,pnl=0.))
        for t in trades:
            g=groups[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"];g['count']+=1;g['pnl']+=t['pnl']
        cases.append(dict(year=key[0],cost=key[1],checks='passed',metrics=result['metrics'],parent_metrics=p['result']['metrics'],
            frequency=entry_frequency(trades,key[0]),added_low_atr_fills=added,displaced_parent_trades=missing,grouped=dict(groups),
            parent_executed_price_pnl=sum(t['pnl']+t['fees']-t['funding'] for t in p['result']['trades']),
            child_executed_price_pnl=sum(t['pnl']+t['fees']-t['funding'] for t in trades)))
    improved=all(c['metrics']['total_return']>c['parent_metrics']['total_return'] and c['metrics']['maximum_drawdown']>=c['parent_metrics']['maximum_drawdown'] for c in cases)
    lines=['# 舊1H ATR門檻消融：檢討與完整比較','',
        '父portfolio_swing_failure_exit → portfolio_sweep_no_atr_floor。只移除短線ATR14/close≥0.006，不繼承斜率risk候選。保留掃單＋三根確認、結構stop、4h方向、原退出／波段失效退出、共用風控、daily2與1x。',
        '每年10,000 USDT，正常單邊費10bps／滑價5bps，雙成本20bps／10bps，含實際mark/funding。全部四筆父指紋與完整結果重現後才跑候選。事前設計及原始訊號盤點見atr-ablation-design.md與data/atr-gate-diagnostics.json。','',
        '|年|成本|父收益|子收益|父DD|子DD|總筆數|短線筆數|',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for c in cases:
        p,m=c['parent_metrics'],c['metrics'];f=c['frequency']
        lines.append(f"|{c['year']}|{c['cost']}|{p['total_return']:+.3%}|{m['total_return']:+.3%}|{p['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{m['number_of_trades']}|{f['intraday']}|")
    lines+=['',('四組收益與回撤均改善，可保留研究候選。' if improved else '未全面改善，不採用為研究基準；原portfolio_swing_failure_exit保留。'),
        '檢討：ATR門檻不是短線稀少的主因，完整掃單＋下一根強收盤＋三根結構＋4h方向交集本來很少；移除前原始訊號19/16，移除後26/29，尚未計每日名額／風控與退出。不能承諾每天1–2。',
        '新增交易品質與費用占比需一起看，交易更多不是有效優勢；下方列出新增低ATR成交與被擠掉的原交易（包含原贏家），不得將舊PnL直接相減當子策略收益。',
        '254項pytest通過，逐筆入場/stop/數量與成本風險推導、breakout邊界、共享gross/stoprisk/margin、cash及每日2單均核對。',
        '2024/2025與本診斷全部是調參，沒有未見驗證；年10%目標未達。MMR2%未驗證歷史級距、1h OHLC路徑、深度滑價、precision/min量與虛擬lot映射限制保留。沒有paper/testnet/live升級。']
    for c in cases:lines+=['',f"## {c['year']}／成本{c['cost']}倍：全部指標與新增交易",'','```json',json.dumps(c,ensure_ascii=False,indent=2),'```']
    Path('docs/research/2026-10-28-atr-ablation-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=[ppath,cpath,tpath,Path(__file__),Path('scripts/research_atr_ablation.py'),Path('scripts/analyze_atr_gate.py'),Path('data/atr-gate-diagnostics.json'),
        Path('app/strategies/directional_intraday.py'),Path('app/strategies/sweep_no_atr_floor.py'),Path('app/backtest/portfolio_research.py'),
        Path('scripts/research_portfolio_overlap.py'),Path('app/risk/regime.py'),Path('data/btc-perpetual-1h/markPriceKlines.json'),Path('data/btc-perpetual-1h/funding-api.json')]
    Path('data/atr-ablation-audit.json').write_text(json.dumps(dict(status='completed_research_candidate',independent_validation=False,
        adopted=improved,source_sha256={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},cases=cases),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(adopted=improved,cases=[dict(year=c['year'],cost=c['cost'],added=len(c['added_low_atr_fills']),added_pnl=sum(t['pnl'] for t in c['added_low_atr_fills'])) for c in cases]),indent=2))


if __name__=='__main__':main()
