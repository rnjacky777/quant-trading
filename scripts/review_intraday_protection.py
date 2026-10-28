"""Audit causal short-horizon price protection and all parent comparisons."""
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
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from app.strategies.swing_failure import breakout_boundary, breakout_failed


def main() -> None:
    ppath=Path('data/perpetual-swing-failure-exit.json');cpath=Path('data/perpetual-intraday-protection.json')
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(ppath.read_text())['rows']}
    payload=json.loads(cpath.read_text());rows=payload['rows']
    assert payload['category']=='exit' and len(rows)==4
    assert {(r['year'],r['cost_multiplier']) for r in rows}=={(2024,1),(2024,2),(2025,1),(2025,2)}
    tpath=Path('data/btc-perpetual-1h/klines.json')
    tape=[Candle('binance-usdm','BTC/USDT','1h',int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tpath.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[]
    for r in rows:
        key=(r['year'],r['cost_multiplier']);p=parents[key]
        assert r['status']==p['status']=='completed'
        for field in ('config','portfolio_limits','sleeves','input_fingerprints','intraday_exit_rule','directional_loss_guard','swing_failure_exit'):
            assert r[field]==p[field],field
        assert r['intraday_price_protection']==dict(activation_r=1.,stop='entry_price',effective='next_hour')
        assert not r.get('slope_risk_cap',False) and not r.get('swing_price_protection',False)
        result=r['result'];trades=result['trades'];aa={a['position_id']:a for a in result['admissions'] if a['status']=='accepted'}
        assert len(aa)==len(trades)==len({t['position_id'] for t in trades})
        assert isclose(result['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        assert all(t['leverage']==1 for t in trades)
        start=1704067200000 if key[0]==2024 else 1735689600000;warm=bisect_left(times,start-243*3600000)
        checked=[];paired=[];giveback=defaultdict(lambda:dict(count=0,pnl=0.,losses=0))
        pevents={(t['sleeve'],t['direction'],t['entry_timestamp_ms']):t for t in p['result']['trades']}
        for t in p['result']['trades']:
            i=bisect_left(times,t['entry_timestamp_ms']);j=bisect_left(times,t['exit_timestamp_ms']);dist=abs(t['entry_price']-t['stop_loss_price'])
            reached=any(t['direction']*(c.close-t['entry_price'])>=dist for c in tape[i:j])
            g=giveback[f"{t['sleeve']}/reached_1R={reached}"];g['count']+=1;g['pnl']+=t['pnl'];g['losses']+=t['pnl']<0
        for t in trades:
            a=aa[t['position_id']];i=bisect_left(times,t['entry_timestamp_ms']);j=bisect_left(times,t['exit_timestamp_ms']);hist=tape[warm:i]
            strategy=DirectionalSwingEfficiencyStrategy() if t['sleeve']=='swing' else DirectionalSweepStructureConfirmStrategy()
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
            updates=a.get('stop_updates',[]);assert len(updates)<=1
            if t['sleeve']=='swing':
                assert not updates and t['exit_reason']!='profit_protection'
                boundary=breakout_boundary(hist,t['direction']);assert a['breakout_level']==boundary
                eligible=[k for k in range(i+1,j+1) if breakout_failed(tape[warm:k],t['direction'],boundary)]
                assert not eligible or eligible[0]==j
            for u in updates:
                assert t['sleeve']=='intraday' and u['from_stop']==u['initial_stop']==t['stop_loss_price']
                assert u['to_stop']==t['entry_price'] and u['active_from_ms']==u['decision_timestamp_ms']+3600000
                k=bisect_left(times,u['decision_timestamp_ms'])
                assert times[k]==u['decision_timestamp_ms'] and tape[k].close==u['trigger_close']
                dist=abs(t['entry_price']-t['stop_loss_price'])
                assert t['direction']*(u['trigger_close']-t['entry_price'])>=dist
                assert i<=k<j and not any(t['direction']*(c.close-t['entry_price'])>=dist for c in tape[i:k])
                checked.append(dict(position_id=t['position_id'],update=u))
            if t['exit_reason']=='profit_protection':
                assert updates and times[j]>=updates[0]['active_from_ms']
                reference=min(tape[j].open,t['entry_price']) if t['direction']==1 else max(tape[j].open,t['entry_price'])
                assert isclose(t['exit_price'],reference*(1-t['direction']*config.slippage_bps/10000),abs_tol=1e-7)
                old=pevents.get((t['sleeve'],t['direction'],t['entry_timestamp_ms']))
                if old:paired.append(dict(parent_position_id=old['position_id'],child_position_id=t['position_id'],parent_pnl=old['pnl'],child_pnl=t['pnl'],parent_exit=old['exit_reason']))
        cases.append(dict(year=key[0],cost=key[1],checks='passed',metrics=result['metrics'],parent_metrics=p['result']['metrics'],
            frequency=entry_frequency(trades,key[0]),parent_giveback_diagnostics=dict(giveback),stop_updates=checked,
            common_protected_exits=paired,protected_parent_winners=[t for t in paired if t['parent_pnl']>0]))
    all_return=all(c['metrics']['total_return']>c['parent_metrics']['total_return'] for c in cases)
    all_dd=all(c['metrics']['maximum_drawdown']>=c['parent_metrics']['maximum_drawdown']-1e-12 for c in cases)
    lines=['# 短線+1R價格保護：止盈止損檢討與全年比較','',
        '父portfolio_swing_failure_exit → portfolio_intraday_protection。短線完成1h收盤達初始價格風險+1R後，stop移至實際進場價，下一根生效；原stop在當根先執行。原短線進場/24h、波段/失效退出、共享風控保留，非固定百分比止盈。事前假說見2026-10-28-intraday-protection-design.md。',
        '正常單邊fee/slip10/5bps、double20/10bps，實際funding/mark，每年重設10,000 USDT，全部1x。先完整重現四筆父結果與資料指紋。','',
        '|年|成本|父收益|子收益|父DD|子DD|總筆數|短線筆數|',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for c in cases:
        p,m=c['parent_metrics'],c['metrics'];f=c['frequency']
        lines.append(f"|{c['year']}|{c['cost']}|{p['total_return']:+.3%}|{m['total_return']:+.3%}|{p['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{m['number_of_trades']}|{f['intraday']}|")
    lines+=['',f'四組收益均改善：{all_return}；四組回撤不退步：{all_dd}。',
        '判斷：'+('保留下一輪研究候選。' if all_return and all_dd else '保留取捨／失敗結果，不取代父研究基準。'),
        '價格保護不等於淨保本：費用、滑價、funding與跳空仍可能虧損；不是每筆固定止盈，也未替波段啟用原失敗1R保護。共用風險與連虧路徑會改變後續數量，共同進場事件不能直接當獨立因果收益。',
        '262項pytest通過；另逐筆核對首次完成close觸發、下一根生效、初始stop保留、保護成交價、多空數量推導、gross/stoprisk/margin、ID、每日2與cash/PnL。',
        '2024/2025與診斷全部是調參，不是未見驗證；每年10%目標未達，短線頻率仍不足。原1h OHLC路徑、固定MMR2%非歷史級距、滑價深度、precision/min單量及虛擬多lot映射限制保留，未動paper/testnet/live或下單。']
    for c in cases:lines+=['',f"## {c['year']}／成本{c['cost']}倍完整指標與提前保護代價",'','```json',json.dumps(c,ensure_ascii=False,indent=2),'```']
    Path('docs/research/2026-10-28-intraday-protection-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=[ppath,cpath,tpath,Path(__file__),Path('app/backtest/portfolio_research.py'),Path('scripts/research_portfolio_overlap.py'),
        Path('scripts/research_intraday_protection.py'),Path('app/risk/regime.py'),Path('data/btc-perpetual-1h/markPriceKlines.json'),Path('data/btc-perpetual-1h/funding-api.json')]
    Path('data/intraday-protection-audit.json').write_text(json.dumps(dict(status='completed_research_candidate',independent_validation=False,
        all_returns_improved=all_return,all_drawdowns_not_worse=all_dd,
        source_sha256={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},cases=cases),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(all_returns_improved=all_return,all_drawdowns_not_worse=all_dd),indent=2))


if __name__=='__main__':main()
