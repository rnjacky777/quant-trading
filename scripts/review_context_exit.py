"""Verify inherited risk guard and record the cost of removing channel exits."""
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
from app.risk.regime import directional_loss_guard_multiplier
from app.strategies.sweep_context_exit import DirectionalSweepContextExitStrategy
from app.strategies.sweep_structural_stop import DirectionalSweepStructuralStopStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy


def main() -> None:
    parent_path=Path("data/perpetual-directional-loss-guard.json")
    child_path=Path("data/perpetual-sweep-context-exit.json")
    diagnostic_path=Path("data/channel-exit-diagnostics.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    diagnostics={(r['year'],r['cost']):r for r in json.loads(diagnostic_path.read_text())['cases']}
    payload=json.loads(child_path.read_text());rows=payload['rows']
    assert payload['category']=='exit' and len(rows)==4
    assert {(r['year'],r['cost_multiplier']) for r in rows}==set(parents)
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[];details=[]
    lines=["# 移除1H通道退出：未採用，保留上一研究候選", "", "2026-10-28。portfolio_directional_loss_guard → portfolio_sweep_context_exit。唯一exit變更：短線只因結構stop、4h反轉或24h上限退出，不再用1h反向10根通道；波段及原同方向連虧guard全部繼承。", "",
        "## 事前證據與限制", "", "父channel-only退出2024一般成本10筆約−46.24USDT、2025為8筆−5.67，但2025空單子組+16.03是贏家，不把全部退出都視為可刪的輸家。這只支持一次試驗，不等於不退出可回收損失。未延長24h（不同於已失敗48h），未掃channel根數。", "",
        "## 全部期間及成本", "", "每年10,000USDT，原訊號、結構初始stop、0.25%／0.125%風險、共享／同方向保護、gross/stoprisk/margin、每日總計2次均不變；實際1x。一般單邊費10bps／滑價5bps，雙成本20bps／10bps，含實際funding。父四筆完整快照（含guard trace）與輸入指紋重播一致後才跑子候選。", "",
        "|年|成本倍數|父收益|候選收益|父回撤|候選回撤|交易數|", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        key=(row['year'],row['cost_multiplier']);parent=parents[key]
        assert row['status']==parent['status']=='completed'
        assert row['directional_loss_guard']==parent['directional_loss_guard'] is True
        for field in ('config','portfolio_limits','input_fingerprints'):
            assert row[field]==parent[field]
        assert row['intraday_exit_rule']==DirectionalSweepContextExitStrategy.name
        for new,old in zip(row['sleeves'],parent['sleeves'],strict=True):
            assert new['name']==old['name'] and new['config']==old['config']
            if new['name']=='swing':
                assert new==old
        result=row['result'];trades=result['trades'];m=result['metrics'];pm=parent['result']['metrics']
        assert not m['liquidation_count'] and not row['portfolio_limits']['same_direction_risk_decay']
        assert isclose(result['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert len({t['position_id'] for t in trades})==len(trades)
        assert all(t['leverage']==1 for t in trades)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        accepted={a['position_id']:a for a in result['admissions'] if a['status']=='accepted'}
        assert set(accepted)=={t['position_id'] for t in trades}
        configs={s['name']:replace(PerpetualResearchConfig(**s['config']),
            max_exposure=min(s['config']['max_exposure'],row['portfolio_limits']['max_gross_exposure'])) for s in row['sleeves']}
        warmup=bisect_left(times,(1704067200000 if row['year']==2024 else 1735689600000)-243*3600000)
        for a in accepted.values():
            i=bisect_left(times,a['timestamp_ms']);entry=tape[i];trace=a['loss_guard_trace'];c=configs[a['sleeve']]
            known=[t for t in trades if t['exit_timestamp_ms']<entry.timestamp_ms or
                t['exit_timestamp_ms']==entry.timestamp_ms and t['entry_timestamp_ms']<entry.timestamp_ms and
                (t['exit_reason'] in {'signal','time_limit'} or
                 t['exit_reason']=='stop_loss' and t['direction']*(entry.open-t['stop_loss_price'])<=0)]
            shared=[t['pnl'] for t in known if t['sleeve']==a['sleeve']]
            own=[t['pnl'] for t in known if t['sleeve']==a['sleeve'] and t['direction']==a['direction']]
            assert trace['shared_pnls']==shared and trace['directional_pnls']==own
            expected=directional_loss_guard_multiplier(shared,own)
            assert trace['final_brake_multiplier']==trace['sizing_multiplier']==expected
            strategy=DirectionalSweepContextExitStrategy() if a['sleeve']=='intraday' else DirectionalSwingEfficiencyStrategy()
            signal=strategy.generate(tape[warmup:i])
            if a['sleeve']=='intraday':
                original=DirectionalSweepStructuralStopStrategy().generate(tape[warmup:i])
                for field in ('action','direction','strength','timestamp','stop_loss_price'):
                    assert getattr(signal,field)==getattr(original,field)
            _,proposal=LongShortResearchEngine(c)._open(a['equity_before'],entry,signal,expected)
            assert proposal is not None
            assert isclose(proposal.quantity*a['scale'],a['quantity'],abs_tol=1e-10)
            assert isclose(proposal.planned_risk*a['scale'],a['planned_risk'],abs_tol=1e-7)
            eq=a['equity_before'];limits=row['portfolio_limits']
            assert a['planned_risk']<=eq*c.risk_per_trade*expected+1e-7
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
        p_events={(t['entry_timestamp_ms'],t['sleeve'],t['direction']):t for t in parent['result']['trades']}
        c_events={(t['entry_timestamp_ms'],t['sleeve'],t['direction']):t for t in trades}
        assert p_events.keys()==c_events.keys()
        cohort_ids={e['position_id'] for e in diagnostics[key]['events'] if e['kind']=='channel_only'}
        common=[];channel=[];grouped=defaultdict(lambda:dict(count=0,pnl=0.))
        for event,t in c_events.items():
            p=p_events[event]
            assert t['entry_price']==p['entry_price'] and t['stop_loss_price']==p['stop_loss_price']
            if t['sleeve']=='swing':
                assert t['exit_price']==p['exit_price'] and t['exit_timestamp_ms']==p['exit_timestamp_ms'] and t['exit_reason']==p['exit_reason']
            repriced=t['pnl']/t['quantity']*p['quantity']
            comparison=dict(entry_timestamp_ms=t['entry_timestamp_ms'],sleeve=t['sleeve'],direction=t['direction'],
                parent_pnl=p['pnl'],child_pnl=t['pnl'],parent_exit=p['exit_reason'],child_exit=t['exit_reason'],
                repriced_parent_qty_delta=repriced-p['pnl'],quantity_delta=t['pnl']-repriced)
            common.append(comparison)
            if p['position_id'] in cohort_ids:
                channel.append(comparison)
            g=grouped[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"]
            g['count']+=1;g['pnl']+=t['pnl']
        assert isclose(sum(e['repriced_parent_qty_delta']+e['quantity_delta'] for e in common),
            sum(t['pnl'] for t in trades)-sum(t['pnl'] for t in parent['result']['trades']),abs_tol=1e-7)
        f=entry_frequency(trades,row['year'])
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{pm['total_return']:+.3%}|{m['total_return']:+.3%}|{pm['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|")
        evidence=dict(year=row['year'],cost=row['cost_multiplier'],checks="passed",metrics=m,frequency=f,
            grouped=dict(grouped),past_only_risk_trace_checks=len(accepted),common_events=common,
            channel_only_comparison=dict(count=len(channel),parent_pnl=sum(e['parent_pnl'] for e in channel),
                child_pnl=sum(e['child_pnl'] for e in channel),new_exit_counts=dict(Counter(e['child_exit'] for e in channel)),events=channel))
        cases.append(evidence)
        details += ["",f"## {row['year']}／成本{row['cost_multiplier']}倍完整指標及共同事件", "",
            "收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding及頻率：", "",
            "```json",json.dumps(evidence,indent=2),"```"]
    lines += ["", "## 決策：不採用", "", "只有2025一般成本−2.454%→−2.297%微升；2024一般成本+3.570%→+3.389%、雙成本+0.328%→+0.252%，2025雙成本−3.617%→−3.691%均退步，四組回撤亦全變大。仍保留父『結構止損＋同方向連虧保護』作下一輪研究基準，沒有新可用／實盤版本。", "",
        "當初channel-only共同事件一般成本2024原淨−46.24→候選−70.86，10筆中3筆轉stop、7筆time_limit；2025為−5.67→−14.93，8筆中4筆stop、3筆time_limit、1筆4h signal退出。因此拿掉虧損退出不等於回收損失。2025一般年度微升，卻不是該退出群組實際改善，還受到其他事件數量與連虧風險路徑影響。共同事件的按父qty重算差額與qty差額是代數拆解，非獨立因果估計。", "",
        "本輪停止，不再掃通道根數或延長持有到數字變好。尚未達各年10%目標；後續優先尋找能改善訊號本身的新證據，而非繼續堆出場補丁。", "",
        "## 驗證及限制", "", "238項pytest通過，新增多空對稱channel-only移除、4h反轉仍退出、原進場／stop／timestamp保留及前綴因果。父四筆完整快照（包含guard trace）重播一致；子交易事件及入場／stop與父相同，波段退出不變，方向guard所有輸入均由當時可知平倉重建，qty與planned risk重算一致；cash/PnL、ID、每日≤2、1x及gross/stoprisk/margin均核對。", "",
        "2024／2025及14項經驗皆調參，不是未見驗證；重疊事件／成本案例非獨立樣本。保留固定BTC選樣、1h盤中順序、固定MMR2%非歷史級距、深度滑價、精度／最小單量及虛擬部位／交易所映射限制。未改live/paper/testnet、未下單。完整曲線交易data/perpetual-sweep-context-exit.json，審計data/context-exit-audit.json。"]
    report=Path("docs/research/2026-10-28-context-exit-results.md")
    report.write_text("\n".join(lines+details)+"\n",encoding="utf-8")
    paths=[parent_path,child_path,diagnostic_path,tape_path,Path(__file__),Path("app/strategies/sweep_context_exit.py"),
        Path("app/backtest/portfolio_research.py"),Path("app/risk/regime.py"),Path("scripts/research_context_exit.py"),Path("scripts/research_portfolio_overlap.py")]
    Path("data/context-exit-audit.json").write_text(json.dumps(dict(status="completed_not_adopted",independent_validation=False,
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},cases=cases),indent=2),encoding="utf-8")
    print(f"Four cases, inherited guard and changed exits audited: {report}")


if __name__=="__main__":
    main()
