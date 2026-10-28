"""Frozen-pair review and causal entry/risk audits for the volume candidate."""
from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import replace
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.frequency import entry_frequency
from app.backtest.long_short_research import LongShortResearchEngine, PerpetualResearchConfig
from app.data.aggregation import completed_four_hour_bars
from app.data.models import Candle
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from app.strategies.swing_volume import DirectionalSwingVolumeStrategy
from app.strategies.swing_failure import breakout_boundary, breakout_failed


def main() -> None:
    ppath=Path('data/perpetual-swing-failure-exit.json');cpath=Path('data/perpetual-swing-volume.json')
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(ppath.read_text())['rows']}
    payload=json.loads(cpath.read_text());rows=payload['rows']
    assert payload['category']=='signal' and payload['parent']=='portfolio_swing_failure_exit'
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
        assert not r.get('slope_risk_cap',False)
        for a,b in zip(r['sleeves'],p['sleeves'],strict=True):
            assert a['name']==b['name'] and a['config']==b['config']
            assert a['strategy']==(DirectionalSwingVolumeStrategy.name if a['name']=='swing' else b['strategy'])
        result=r['result'];trades=result['trades'];aa={a['position_id']:a for a in result['admissions'] if a['status']=='accepted'}
        assert len(aa)==len(trades)==len({t['position_id'] for t in trades})
        assert isclose(result['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert all(t['leverage']==1 for t in trades)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        start=1704067200000 if key[0]==2024 else 1735689600000;warm=bisect_left(times,start-243*3600000)
        for t in trades:
            a=aa[t['position_id']];i=bisect_left(times,t['entry_timestamp_ms']);j=bisect_left(times,t['exit_timestamp_ms']);hist=tape[warm:i]
            strategy=DirectionalSwingVolumeStrategy() if t['sleeve']=='swing' else DirectionalSweepStructureConfirmStrategy()
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
                old=DirectionalSwingEfficiencyStrategy().generate(hist)
                assert old.direction==signal.direction and old.stop_loss_price==signal.stop_loss_price
                b=completed_four_hour_bars(hist)
                assert b[-1].volume>=sum(c.volume for c in b[-21:-1])/20
                boundary=breakout_boundary(hist,t['direction']);assert a['breakout_level']==boundary
                eligible=[k for k in range(i+1,j+1) if breakout_failed(tape[warm:k],t['direction'],boundary)]
                assert not eligible or eligible[0]==j
                if t['exit_reason']=='breakout_failure':assert eligible
        filtered=[];groups=defaultdict(lambda:dict(count=0,pnl=0.));parent_groups=defaultdict(lambda:dict(count=0,pnl=0.))
        for t in p['result']['trades']:
            if t['sleeve']!='swing':continue
            i=bisect_left(times,t['entry_timestamp_ms']);hist=tape[warm:i];bars=completed_four_hour_bars(hist)
            passes=bars[-1].volume>=sum(c.volume for c in bars[-21:-1])/20
            g=parent_groups[f"{t['direction']}/volume_pass={passes}"];g['count']+=1;g['pnl']+=t['pnl']
            if not passes:
                assert DirectionalSwingVolumeStrategy().generate(hist).direction==0
                filtered.append(dict(position_id=t['position_id'],direction=t['direction'],pnl=t['pnl'],
                    confirmation_volume=bars[-1].volume,prior20_mean=sum(c.volume for c in bars[-21:-1])/20))
        for t in trades:
            g=groups[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"];g['count']+=1;g['pnl']+=t['pnl']
        cases.append(dict(year=key[0],cost=key[1],checks='passed',metrics=result['metrics'],parent_metrics=p['result']['metrics'],
            frequency=entry_frequency(trades,key[0]),parent_volume_groups=dict(parent_groups),filtered_parent_trades=filtered,
            filtered_parent_winners=[t for t in filtered if t['pnl']>0],grouped=dict(groups)))
    all_returns=all(c['metrics']['total_return']>c['parent_metrics']['total_return'] for c in cases)
    all_dd=all(c['metrics']['maximum_drawdown']>=c['parent_metrics']['maximum_drawdown'] for c in cases)
    lines=['# 波段確認成交量：檢討與全年比較','',
        '父portfolio_swing_failure_exit → portfolio_swing_volume；只加確認4h volume≥之前20根4h平均量。短線及原波段退出／固定失效邊界、風控全部保留。未沿用斜率risk或移除ATR候選。事前設計見2026-10-28-swing-volume-design.md。',
        '每年本金10,000 USDT、1x，正常單邊fee/slip10/5bps、double20/10bps，含實際mark/funding。四筆父完整快照與資料指紋一致後才測子候選。','',
        '|年|成本|父收益|子收益|父DD|子DD|總筆數|短線筆數|',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for c in cases:
        p,m=c['parent_metrics'],c['metrics'];f=c['frequency']
        lines.append(f"|{c['year']}|{c['cost']}|{p['total_return']:+.3%}|{m['total_return']:+.3%}|{p['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{m['number_of_trades']}|{f['intraday']}|")
    lines+=['',f'四組收益全升：{all_returns}；四組回撤均不退步：{all_dd}。',
        '判斷：'+('保留下一輪研究候選，非實盤優勢證明。' if all_returns and all_dd else '不是全面升級，不取代原portfolio_swing_failure_exit研究基準，保留取捨／失敗證據。'),
        '少量低量交易分組雖虧，排除後仍有共享資金、連虧guard及名額路徑改變；不可用舊PnL相減推算新收益。排除原贏家逐筆保留如下。',
        '2024/2025與成交量分組都是調參，不能叫未見驗證；目前每年10%目標未達。此規則會減少波段訊號，不解決短線18/16筆的頻率；不把成交量當勝率或加槓桿理由。',
        '256項pytest通過；核對完成4h volume不含確認bar的歷史基準、入場/stop、成本risk sizing、gross/stoprisk/margin、cash/PnL、daily2與獨立lot失效邊界。',
        'MMR2%非已驗證歷史級距、1h OHLC盤中路徑、precision/min量、滑價深度與虛擬lot映射限制保留。無交易所訂單／paper/testnet/live變更。']
    for c in cases:lines+=['',f"## {c['year']}／成本{c['cost']}倍完整指標與排除代價",'','```json',json.dumps(c,ensure_ascii=False,indent=2),'```']
    Path('docs/research/2026-10-28-swing-volume-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=[ppath,cpath,tpath,Path(__file__),Path('app/strategies/swing_volume.py'),Path('scripts/research_swing_volume.py'),
        Path('scripts/research_portfolio_overlap.py'),Path('app/backtest/portfolio_research.py'),Path('app/risk/regime.py'),
        Path('data/btc-perpetual-1h/markPriceKlines.json'),Path('data/btc-perpetual-1h/funding-api.json')]
    Path('data/swing-volume-audit.json').write_text(json.dumps(dict(status='completed_research_candidate',independent_validation=False,
        all_returns_improved=all_returns,all_drawdowns_not_worse=all_dd,
        source_sha256={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},cases=cases),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(all_returns_improved=all_returns,all_drawdowns_not_worse=all_dd),indent=2))


if __name__=='__main__':main()
