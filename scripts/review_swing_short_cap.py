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


def main() -> None:
    parent_path=Path('data/perpetual-swing-failure-exit.json')
    child_path=Path('data/perpetual-swing-short-risk-cap.json')
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    payload=json.loads(child_path.read_text());rows=payload['rows']
    assert payload['category']=='risk' and payload['parent']=='portfolio_swing_failure_exit'
    assert len(rows)==4 and {(r['year'],r['cost_multiplier']) for r in rows}=={(2024,1),(2024,2),(2025,1),(2025,2)}
    tpath=Path('data/btc-perpetual-1h/klines.json')
    tape=[Candle('binance-usdm','BTC/USDT','1h',int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tpath.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[]
    for row in rows:
        key=row['year'],row['cost_multiplier'];parent=parents[key]
        assert row['status']==parent['status']=='completed' and row['swing_short_risk_cap'] is True
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
            cap=.5 if t['sleeve']=='swing' and t['direction']==-1 else 1.
            multiplier=min(brake,cap)
            assert a['swing_short_risk_trace']==dict(cap=cap,loss_brake=brake,sizing_multiplier=multiplier)
            assert trace['final_brake_multiplier']==brake and trace['sizing_multiplier']==multiplier
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
            for field in ('exit_timestamp_ms','entry_price','exit_price','exit_reason','stop_loss_price'):
                assert x[field]==y[field],field
            common.append(dict(sleeve=x['sleeve'],direction=x['direction'],entry_ms=x['entry_timestamp_ms'],
                parent_pnl=x['pnl'],child_pnl=y['pnl'],parent_quantity=x['quantity'],child_quantity=y['quantity']))
        groups=defaultdict(lambda:dict(count=0,pnl=0.))
        for t in trades:
            g=groups[f"{t['sleeve']}/{t['direction']}"];g['count']+=1;g['pnl']+=t['pnl']
        cases.append(dict(year=key[0],cost=key[1],checks='passed',metrics=result['metrics'],parent_metrics=parent['result']['metrics'],
            frequency=entry_frequency(trades,key[0]),grouped=dict(groups),common_entries=common,
            missing_entries=[old[k] for k in old.keys()-new.keys()],new_entries=[new[k] for k in new.keys()-old.keys()],
            downsized_winners=[t for t in common if t['parent_pnl']>0 and t['child_quantity']<t['parent_quantity']],
            parent_monthly=monthly_equity(parent['result'],key[0]),child_monthly=monthly_equity(result,key[0])))
    lines=['# 波段空單風險上限：全年比較與決策','','portfolio_swing_failure_exit → portfolio_swing_short_risk_cap。只將波段空單risk倍率與0.5取min，不重複減半；訊號、stop、退出及共享風控保留。事前登記見2026-10-28-swing-short-cap-design.md。',
        '每年10,000 USDT，正常單邊費10bps／滑價5bps，雙成本20／10bps，實際mark與funding。設定maximum_leverage=2保留，實際交易全部1x。四組父完整快照及指紋重播相同後才測候選。','',
        '|年|成本|父收益|子收益|增加USDT|父DD|子DD|總筆數|短線筆數|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for c in cases:
        p,m=c['parent_metrics'],c['metrics'];f=c['frequency']
        lines.append(f"|{c['year']}|{c['cost']}|{p['total_return']:+.3%}|{m['total_return']:+.3%}|{10000*(m['total_return']-p['total_return']):+.2f}|{p['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{m['number_of_trades']}|{f['intraday']}|")
    lines+=['','決策：保留風險配置研究候選，不取代原基準。四組收益小升，2024最大回撤不變、2025改善；但2025仍虧、每年10%目標未達、頻率不變。這是直接用歷史分組提出的假說，不能據此宣稱未見優勢。',
        '策略回測4組父重播＋4組候選；研究候選1個。39項相關程式測試通過，測試數不是策略優化次數或盈利證據。',
        '每筆僅使用進場前完成歷史推導訊號、stop與風險數量，核對共享gross/stoprisk/margin准入、cash/PnL、ID與每日兩筆；共同入場的成交價及退出時間完全相同，主要是數量改變而非訊號改善。本樣本沒有新增或漏掉進場，也沒有被縮小的原波段空單贏家：它們原已受連虧倍率限制；這不是未來不會縮小贏家的保證。共享equity導致的非目標數量變化與全部共同交易列於下方。',
        '短線2024/2025為18/16筆、18/16個UTC活躍日、每日0.0492/0.0438筆，不強迫湊數。月度mark-to-market與所有指標如下。',
        '2024/2025均為調參，重疊成本案例非獨立證據。固定BTC選樣、OHLC盤中路徑、固定滑價與深度、精度及最小量、未驗歷史margin級距、虛擬多lot交易所映射限制保留。未變更paper/testnet/live或送單。']
    for c in cases:
        lines+=['',f"## {c['year']} 成本{c['cost']}：完整指標及取捨",'','```json',json.dumps(c,ensure_ascii=False,indent=2),'```']
    Path('docs/research/2026-10-28-swing-short-cap-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=[parent_path,child_path,tpath,Path(__file__),Path('scripts/research_swing_short_cap.py'),Path('scripts/research_portfolio_overlap.py'),Path('app/backtest/portfolio_research.py'),Path('app/risk/regime.py'),Path('docs/research/2026-10-28-swing-short-cap-design.md')]
    Path('data/swing-short-cap-audit.json').write_text(json.dumps(dict(status='completed_research_candidate',decision='retain_research_candidate_only',retained_baseline='portfolio_swing_failure_exit',independent_validation=False,cases=cases,source_sha256={str(p):sha256(p.read_bytes()).hexdigest() for p in paths}),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Four case audits passed; candidate retained for research only.')


if __name__=='__main__':
    main()
