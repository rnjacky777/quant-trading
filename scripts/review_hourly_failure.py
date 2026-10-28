"""Audit risk sizing against completed history and report all frozen cases."""
from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import replace
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.frequency import entry_frequency
from app.backtest.path_diagnostics import monthly_equity
from app.backtest.long_short_research import LongShortResearchEngine, PerpetualResearchConfig
from app.data.models import Candle
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from app.strategies.swing_failure import breakout_boundary, breakout_failed


def main() -> None:
    parent_path=Path('data/perpetual-swing-failure-exit.json')
    child_path=Path('data/perpetual-swing-hourly-failure.json')
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    payload=json.loads(child_path.read_text());rows=payload['rows']
    assert payload['category']=='exit' and payload['parent']=='portfolio_swing_failure_exit'
    assert len(rows)==4 and {(r['year'],r['cost_multiplier']) for r in rows}=={(2024,1),(2024,2),(2025,1),(2025,2)}
    tpath=Path('data/btc-perpetual-1h/klines.json')
    tape=[Candle('binance-usdm','BTC/USDT','1h',int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tpath.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[]
    for row in rows:
        key=row['year'],row['cost_multiplier'];parent=parents[key]
        assert row['status']==parent['status']=='completed' and row['swing_hourly_failure'] is True
        for field in ('sleeves','config','portfolio_limits','input_fingerprints','directional_loss_guard','swing_failure_exit','intraday_exit_rule'):
            assert row[field]==parent[field],field
        result=row['result'];trades=result['trades']
        admissions={a['position_id']:a for a in result['admissions'] if a['status']=='accepted'}
        assert len(admissions)==len(trades)==len({t['position_id'] for t in trades})
        assert isclose(result['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert all(t['leverage']==1 for t in trades)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        start=1704067200000 if key[0]==2024 else 1735689600000
        warm=bisect_left(times,start-243*3600000)
        for t in trades:
            a=admissions[t['position_id']];i=bisect_left(times,t['entry_timestamp_ms'])
            strategy=DirectionalSwingEfficiencyStrategy() if t['sleeve']=='swing' else DirectionalSweepStructureConfirmStrategy()
            signal=strategy.generate(tape[warm:i])
            assert signal.direction==t['direction'] and isclose(signal.stop_loss_price,t['stop_loss_price'],abs_tol=1e-7)
            config=PerpetualResearchConfig(**next(s['config'] for s in row['sleeves'] if s['name']==t['sleeve']))
            config=replace(config,max_exposure=min(config.max_exposure,row['portfolio_limits']['max_gross_exposure']))
            trace=a['loss_guard_trace'];brake=min(trace['shared_multiplier'],trace['directional_multiplier'])
            multiplier=brake
            assert trace['final_brake_multiplier']==brake and trace['sizing_multiplier']==multiplier
            if t['sleeve']=='swing':
                boundary=breakout_boundary(tape[warm:i],t['direction'])
                assert a['breakout_level']==boundary
                j=bisect_left(times,t['exit_timestamp_ms'])
                eligible=[k for k in range(i+1,j+1) if breakout_failed(tape[warm:k],t['direction'],boundary,hourly=True)]
                assert not eligible or eligible[0]==j
                if t['exit_reason']=='breakout_failure':
                    assert eligible and eligible[0]==j
                    assert t['exit_price']==tape[j].open*(1-t['direction']*row['config']['slippage_bps']/10000)
            _,proposal=LongShortResearchEngine(config)._open(a['equity_before'],tape[i],signal,multiplier)
            assert proposal is not None
            assert isclose(a['quantity'],proposal.quantity*a['scale'],abs_tol=1e-10)
            assert isclose(a['planned_risk'],proposal.planned_risk*a['scale'],abs_tol=1e-7)
            eq=a['equity_before'];limits=row['portfolio_limits']
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
        def identity(t: dict) -> tuple:
            return t['sleeve'],t['direction'],t['entry_timestamp_ms']
        old={identity(t):t for t in parent['result']['trades']};new={identity(t):t for t in trades}
        common=[]
        for k in sorted(old.keys() & new.keys()):
            x,y=old[k],new[k]
            for field in ('entry_price','stop_loss_price'):
                assert x[field]==y[field],field
            common.append(dict(sleeve=x['sleeve'],direction=x['direction'],entry_ms=x['entry_timestamp_ms'],
                parent_pnl=x['pnl'],child_pnl=y['pnl'],parent_quantity=x['quantity'],child_quantity=y['quantity'],parent_exit_ms=x['exit_timestamp_ms'],child_exit_ms=y['exit_timestamp_ms'],parent_exit=x['exit_reason'],child_exit=y['exit_reason']))
        groups=defaultdict(lambda:dict(count=0,pnl=0.))
        for t in trades:
            g=groups[f"{t['sleeve']}/{t['direction']}"];g['count']+=1;g['pnl']+=t['pnl']
        cases.append(dict(year=key[0],cost=key[1],checks='passed',metrics=result['metrics'],parent_metrics=parent['result']['metrics'],
            frequency=entry_frequency(trades,key[0]),grouped=dict(groups),common_entries=common,
            missing_entries=[old[k] for k in old.keys()-new.keys()],new_entries=[new[k] for k in new.keys()-old.keys()],
            early_exit_winners=[t for t in common if t['parent_pnl']>0 and t['child_exit_ms']<t['parent_exit_ms']],
            parent_monthly=monthly_equity(parent['result'],key[0]),child_monthly=monthly_equity(result,key[0])))
    lines=['# 波段1h失效退出：檢討與完整比較','','portfolio_swing_failure_exit → portfolio_swing_hourly_failure。唯一修改：固定突破邊界以完成1h收盤確認失效，下一根open退出；不繼承空單減倉候選。事前登記見2026-10-28-hourly-failure-design.md。',
        '每年10,000 USDT，正常單邊fee/slippage10/5bps、雙成本20/10bps，原實際mark/funding及風控。實際全部1x。四組父指紋與完整快照重播一致。','',
        '|年|成本|父收益|子收益|增加USDT|父DD|子DD|總筆數|短線筆數|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for c in cases:
        p,m=c['parent_metrics'],c['metrics'];f=c['frequency']
        lines.append(f"|{c['year']}|{c['cost']}|{p['total_return']:+.3%}|{m['total_return']:+.3%}|{10000*(m['total_return']-p['total_return']):+.2f}|{p['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{m['number_of_trades']}|{f['intraday']}|")
    lines+=['','決策：拒絕作為新研究基準，保留portfolio_swing_failure_exit。四組實際回測結果與提前退出贏家如下，不能將原虧損組當可回收收益。',
        '2024正常成本一筆原贏家由+23.53變為−5.07 USDT，雙成本由+19.98變為−5.75；2024正常成本多1筆進場，其餘案例進場集合相同。短線仍18/16筆、18/16個UTC活躍日，每日0.0492/0.0438筆。',
        '策略回測4組父重播＋4組候選；新研究候選1個；36項相關程式測試通過，不能當作收益證據。',
        '核對每筆進場前完成歷史訊號、初始stop、原連虧倍率與數量、共享gross/stoprisk/reserved-margin、每日兩筆、ID及cash/PnL；波段固定邊界只用入場前資料，首次完成1h失效最早下一根open退出。優先保留強平、跳空stop、時間／原訊號退出。',
        '原先2025的13筆早期失效皆最終虧損只是事後分組，提早退出可能也縮小其間反彈回收，或改變再入場、連虧及資金路徑。下列共同交易、提前退出贏家、新增／漏掉進場與月度mark-to-market保留完整代價。',
        '2024/2025全部調參，重疊成本案例不是獨立樣本。每年10%與短線頻率目標仍未達，不掃2h/3h或邊界緩衝。',
        '保留固定BTC選樣、OHLC路徑／固定滑價／深度、歷史margin級距未驗、精度與最小量、獨立研究lot至交易所映射限制。未改paper/testnet/live或送單。']
    for c in cases:
        lines+=['',f"## {c['year']} 成本{c['cost']}：完整指標及取捨",'','```json',json.dumps(c,ensure_ascii=False,indent=2),'```']
    Path('docs/research/2026-10-28-hourly-failure-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=[parent_path,child_path,tpath,Path(__file__),Path('scripts/research_hourly_failure.py'),Path('scripts/research_portfolio_overlap.py'),Path('app/backtest/portfolio_research.py'),Path('app/risk/regime.py'),Path('app/strategies/swing_failure.py'),Path('data/hourly-failure-precheck.json'),Path('docs/research/2026-10-28-hourly-failure-design.md')]
    Path('data/hourly-failure-audit.json').write_text(json.dumps(dict(status='completed_research_candidate',decision='reject_preserve_parent',retained_baseline='portfolio_swing_failure_exit',independent_validation=False,cases=cases,source_sha256={str(p):sha256(p.read_bytes()).hexdigest() for p in paths}),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Four case audits passed; candidate comparison saved.')


if __name__=='__main__':
    main()
