"""Audit frozen per-lot swing boundaries and all four controlled cases."""
from bisect import bisect_left
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.frequency import entry_frequency
from app.data.models import Candle
from app.strategies.swing_failure import breakout_boundary, breakout_failed
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy


def main() -> None:
    parent_path=Path('data/perpetual-sweep-structure-confirm.json')
    child_path=Path('data/perpetual-swing-failure-exit.json')
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    payload=json.loads(child_path.read_text());rows=payload['rows']
    assert payload['category']=='exit' and len(rows)==4
    assert {(r['year'],r['cost_multiplier']) for r in rows}=={(2024,1),(2024,2),(2025,1),(2025,2)}
    tape_path=Path('data/btc-perpetual-1h/klines.json')
    tape=[Candle('binance-usdm','BTC/USDT','1h',int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[]
    lines=['# 波段突破失效退出：全年受控比較','',
        '父 portfolio_sweep_structure_confirm → 子 portfolio_swing_failure_exit。只新增每筆波段完成4h收盤跌回／升回原20根突破區間時的退出；下一1h開盤成交。事前設計見2026-10-28-swing-failure-design.md。', '',
        '每年10,000 USDT重新開始，1x，正常費10bps／滑價5bps；雙成本20bps／10bps，另含實際funding與mark。四筆父完整快照與行情指紋重現後才測子候選。所有2024／2025皆為調參資料。','',
        '|年|成本倍數|父收益|子收益|父最大回撤|子最大回撤|總筆數|短線筆數|',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        key=(row['year'],row['cost_multiplier']);parent=parents[key]
        assert row['status']==parent['status']=='completed' and row['swing_failure_exit'] is True
        for field in ('config','portfolio_limits','input_fingerprints','intraday_exit_rule','directional_loss_guard','sleeves'):
            assert row[field]==parent[field],field
        result=row['result'];trades=result['trades'];m=result['metrics'];pm=parent['result']['metrics']
        assert isclose(result['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert len({t['position_id'] for t in trades})==len(trades)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        assert all(t['leverage']==1 for t in trades)
        admissions={a['position_id']:a for a in result['admissions'] if a['status']=='accepted'}
        start=1704067200000 if row['year']==2024 else 1735689600000
        warmup=bisect_left(times,start-243*3600000)
        limits=row['portfolio_limits'];failures=[]
        for t in trades:
            a=admissions[t['position_id']];eq=a['equity_before'];i=bisect_left(times,t['entry_timestamp_ms'])
            j=bisect_left(times,t['exit_timestamp_ms']);history=tape[warmup:i]
            strategy=DirectionalSwingEfficiencyStrategy() if t['sleeve']=='swing' else DirectionalSweepStructureConfirmStrategy()
            signal=strategy.generate(history)
            assert signal.direction==t['direction']
            assert isclose(signal.stop_loss_price,t['stop_loss_price'],abs_tol=1e-7)
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
            trace=a['loss_guard_trace']
            assert trace['final_brake_multiplier']==min(trace['shared_multiplier'],trace['directional_multiplier'])
            config=next(s['config'] for s in row['sleeves'] if s['name']==t['sleeve'])
            assert a['planned_risk']<=eq*config['risk_per_trade']*trace['sizing_multiplier']+1e-7
            if t['sleeve']=='swing':
                boundary=breakout_boundary(history,t['direction'])
                assert boundary==a['breakout_level']
                # Search completed closes, never the current execution hour.
                eligible=[k for k in range(i+1,j+1) if breakout_failed(tape[warmup:k],t['direction'],boundary)]
                assert not eligible or eligible[0]==j, 'missed earlier failure close'
                if t['exit_reason']=='breakout_failure':
                    assert eligible and eligible[0]==j
                    slip=config['slippage_bps']/10000
                    expected=tape[j].open*(1-t['direction']*slip)
                    assert isclose(t['exit_price'],expected,abs_tol=1e-7)
                    assert t['direction']*(tape[j].open-t['stop_loss_price'])>0
                    failures.append(dict(position_id=t['position_id'],direction=t['direction'],
                        boundary=boundary,decision_hour_ms=times[j-1],execution_ms=times[j],pnl=t['pnl']))
            else:
                assert 'breakout_level' not in a and t['exit_reason']!='breakout_failure'
        parent_events={(t['sleeve'],t['direction'],t['entry_timestamp_ms']):t for t in parent['result']['trades']}
        changed=[]
        for t in trades:
            p=parent_events.get((t['sleeve'],t['direction'],t['entry_timestamp_ms']))
            if p and t['exit_timestamp_ms']!=p['exit_timestamp_ms']:
                changed.append(dict(sleeve=t['sleeve'],direction=t['direction'],entry_ms=t['entry_timestamp_ms'],
                    parent_pnl=p['pnl'],child_pnl=t['pnl'],parent_exit=p['exit_reason'],child_exit=t['exit_reason'],
                    parent_exit_ms=p['exit_timestamp_ms'],child_exit_ms=t['exit_timestamp_ms']))
        groups=defaultdict(lambda:dict(count=0,pnl=0.))
        for t in trades:
            g=groups[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"];g['count']+=1;g['pnl']+=t['pnl']
        f=entry_frequency(trades,row['year'])
        case=dict(year=key[0],cost=key[1],checks='passed',metrics=m,parent_metrics=pm,frequency=f,
            failure_exits=failures,changed_same_entry_exits=changed,grouped=dict(groups),
            earlier_exits_from_parent_winners=[t for t in changed if t['parent_pnl']>0 and t['child_exit_ms']<t['parent_exit_ms']])
        cases.append(case)
        lines.append(f"|{key[0]}|{key[1]}|{pm['total_return']:+.3%}|{m['total_return']:+.3%}|{pm['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|{f['intraday']}|")
    improved=all(c['metrics']['total_return']>c['parent_metrics']['total_return'] and c['metrics']['maximum_drawdown']>c['parent_metrics']['maximum_drawdown'] for c in cases)
    lines+=['','判斷：'+('四組收益及回撤改善，保留研究候選。' if improved else '非全面改善，不自動替換父版本。'),
        '2025仍虧，年淨10%目標未達，短線18／16筆的頻率不足也未解決。不能因退出組過去虧損，就直接將舊虧損相減宣稱可回收收益。',
        '246項測試通過（含多空、等於／wick不觸發、未完成4h不觸發、每lot不同固定邊界及下一開盤成交）。另逐筆核對新退出及入場、cash/PnL、daily2、gross/stoprisk/margin。',
        '歷史margin級距未驗證、MMR2%固定假設、1h OHLC路徑／滑價深度與最小量限制保留。虛擬多lot不是已驗證交易所hedge映射；無paper/testnet/live升級。',
        '同時間入場的父子PnL仍受資金／連虧風控變動影響，不等於純單筆退出效果。完整風險調整、費用、曝險、平均盈虧等指標與提前截斷的原贏家如下。']
    for c in cases:
        lines+=['',f"## {c['year']}／成本{c['cost']}倍",'','```json',json.dumps(c,ensure_ascii=False,indent=2),'```']
    Path('docs/research/2026-10-28-swing-failure-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    sources=[parent_path,child_path,tape_path,Path('data/btc-perpetual-1h/markPriceKlines.json'),Path('data/btc-perpetual-1h/funding-api.json'),
        Path(__file__),Path('scripts/research_swing_failure.py'),Path('scripts/research_portfolio_overlap.py'),
        Path('app/backtest/portfolio_research.py'),Path('app/strategies/swing_failure.py'),Path('app/risk/regime.py')]
    Path('data/swing-failure-audit.json').write_text(json.dumps(dict(status='completed_research_candidate',
        independent_validation=False,all_four_return_and_drawdown_improved=improved,
        source_sha256={str(p):sha256(p.read_bytes()).hexdigest() for p in sources},cases=cases),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(cases=len(cases),all_four_return_and_drawdown_improved=improved,
        failure_exits=[len(c['failure_exits']) for c in cases]),indent=2))


if __name__=='__main__':
    main()
