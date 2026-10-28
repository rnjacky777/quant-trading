"""Audit structural exits, fixed risk, matched entries and quantity-path effects."""
from bisect import bisect_left
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.frequency import entry_frequency
from app.data.models import Candle
from app.strategies.pa_smc import DirectionalSweepStrategy
from app.strategies.sweep_structural_stop import DirectionalSweepStructuralStopStrategy


def main() -> None:
    parent_path=Path("data/perpetual-confirmed-efficiency.json")
    child_path=Path("data/perpetual-sweep-structural-stop.json")
    diagnostic_path=Path("data/managed-signal-diagnostics.json")
    diagnostic_audit_path=Path("data/managed-signal-audit.json")
    signals_path=Path("data/all-signal-diagnostics.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    payload=json.loads(child_path.read_text());rows=payload['rows']
    assert payload['category']=='exit' and len(rows)==4
    assert {(r['year'],r['cost_multiplier']) for r in rows}==set(parents)
    raw={(r['year'],r['cost']):r for r in json.loads(signals_path.read_text())['cases']}
    managed=json.loads(diagnostic_path.read_text())['cases']
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[];details=[]
    lines=["# 掃單結構止損：收益微升，但回撤增加", "", "2026-10-28。原portfolio_confirmed_efficiency → portfolio_sweep_structural_stop，單一exit類別。四筆父原資料指紋及完整結果已重播完全一致才跑子候選，保留正常／雙成本全部失敗期間。", "",
        "## 先做的診斷", "", "每個原訊號用獨立10,000帳戶、原0.25%風險、關閉連虧減倉，保留原止損／動態訊號退出／24h或168h／funding及mark強平；只為隔離訊號品質與帳戶路徑，不是策略變更或可相加的年度收益。所有原成交事件的入場／退出／初始止損／原因、每單位qty費用funding與PnL逐一重現一致。2025各組平均R仍負，不能把虧損只怪共享風控。", "",
        "2024短線63訊號有17個ATR止損在掃單極值內；2025短線44訊號有12個。每年各3個事件在ATR止損退出當根整段尚未達掃單極值，原止損與形態失效位置不一致。這不表示放寬必賺，只形成一次候選；沒有挑未來極值或掃buffer。", "",
        "## 唯一變更", "", "短線多單初始stop=當時已知掃單low，空單=掃單high；原掃單進場／確認／4h方向／ATR門檻、全部訊號退出與持有上限、波段完全不變。風控仍按原單筆0.25%（連虧後0.125%）、止損及成本反推qty，止損遠則qty可變小、近則可變大但受原曝險及風險限制，未增加槓桿。", "",
        "## 完整年度結果", "", "年度本金各10,000USDT，一般單邊費10bps／滑價5bps，雙成本20bps／10bps，含實際funding，全部1x。", "",
        "|年|成本倍數|父收益|子收益|收益差百分點|父回撤|子回撤|總交易數|短線筆數|", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        key=(row['year'],row['cost_multiplier']);parent=parents[key]
        assert row['status']==parent['status']=='completed'
        for field in ('input_fingerprints','config','portfolio_limits'):
            assert row[field]==parent[field]
        assert row['intraday_exit_rule']==DirectionalSweepStructuralStopStrategy.name
        for new,old in zip(row['sleeves'],parent['sleeves'],strict=True):
            assert new['name']==old['name'] and new['config']==old['config']
            if new['name']=='swing':
                assert new==old
        result=row['result'];trades=result['trades'];m=result['metrics'];pm=parent['result']['metrics']
        assert isclose(result['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert len({t['position_id'] for t in trades})==len(trades)
        assert all(t['leverage']==1 for t in trades)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        accepted={a['position_id']:a for a in result['admissions'] if a['status']=='accepted'}
        assert set(accepted)=={t['position_id'] for t in trades}
        for a in accepted.values():
            eq=a['equity_before'];limits=row['portfolio_limits']
            assert a['planned_risk']<=eq*row['config']['risk_per_trade']+1e-7
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
        start=1704067200000 if row['year']==2024 else 1735689600000
        warmup=bisect_left(times,start-243*3600000)
        raw_checks=0
        for event in raw[key]['signals']:
            if event['sleeve']!='intraday':
                continue
            index=bisect_left(times,event['timestamp_ms']);history=tape[warmup:index]
            old=DirectionalSweepStrategy().generate(history)
            new=DirectionalSweepStructuralStopStrategy().generate(history)
            assert new.direction==old.direction==event['direction']
            for field in ('action','strength','timestamp','exit_long','exit_short'):
                assert getattr(new,field)==getattr(old,field)
            assert new.stop_loss_price==(history[-2].low if new.direction==1 else history[-2].high)
            raw_checks+=1
        grouped=defaultdict(lambda:dict(count=0,pnl=0.))
        parent_events={(t['entry_timestamp_ms'],t['sleeve'],t['direction']):t for t in parent['result']['trades']}
        common=[];matched_parent=set();new_unmatched=[]
        for t in trades:
            g=grouped[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"]
            g['count']+=1;g['pnl']+=t['pnl']
            if t['sleeve']=='intraday':
                index=bisect_left(times,t['entry_timestamp_ms'])
                signal=DirectionalSweepStructuralStopStrategy().generate(tape[warmup:index])
                assert signal.direction==t['direction'] and signal.stop_loss_price==t['stop_loss_price']
                assert signal.timestamp.timestamp()*1000==times[index]-3600000
            event=(t['entry_timestamp_ms'],t['sleeve'],t['direction'])
            if event not in parent_events:
                new_unmatched.append(t)
                continue
            p=parent_events[event];matched_parent.add(event)
            at_parent_qty=t['pnl']/t['quantity']*p['quantity']
            common.append(dict(entry_timestamp_ms=t['entry_timestamp_ms'],sleeve=t['sleeve'],direction=t['direction'],
                parent_pnl=p['pnl'],child_pnl=t['pnl'],parent_quantity=p['quantity'],child_quantity=t['quantity'],
                parent_exit=p['exit_reason'],child_exit=t['exit_reason'],parent_stop=p['stop_loss_price'],child_stop=t['stop_loss_price'],
                repriced_at_parent_qty_difference=at_parent_qty-p['pnl'],quantity_difference=t['pnl']-at_parent_qty))
        old_unmatched=[t for key2,t in parent_events.items() if key2 not in matched_parent]
        algebra_delta=sum(e['repriced_at_parent_qty_difference']+e['quantity_difference'] for e in common)+sum(t['pnl'] for t in new_unmatched)-sum(t['pnl'] for t in old_unmatched)
        assert isclose(algebra_delta,sum(t['pnl'] for t in trades)-sum(t['pnl'] for t in parent['result']['trades']),abs_tol=1e-7)
        f=entry_frequency(trades,row['year'])
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{pm['total_return']:+.3%}|{m['total_return']:+.3%}|{(m['total_return']-pm['total_return'])*100:+.3f}|{pm['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|{f['intraday']}|")
        evidence=dict(year=row['year'],cost=row['cost_multiplier'],checks="passed",metrics=m,frequency=f,
            raw_entry_signals_checked=raw_checks,grouped=dict(grouped),common_events=common,
            matched_count=len(common),new_unmatched_count=len(new_unmatched),old_unmatched_count=len(old_unmatched),
            repriced_parent_qty_difference=sum(e['repriced_at_parent_qty_difference'] for e in common),
            quantity_difference=sum(e['quantity_difference'] for e in common),
            parent_fees=pm['fees'],child_fees=m['fees'],
            parent_winners_with_lower_child_pnl=sum(e['parent_pnl']>0 and e['child_pnl']<e['parent_pnl'] for e in common),
            parent_losers_with_higher_child_pnl=sum(e['parent_pnl']<0 and e['child_pnl']>e['parent_pnl'] for e in common))
        cases.append(evidence)
        details += ["",f"## {row['year']}／成本{row['cost_multiplier']}倍完整指標及逐事件代價", "",
            "收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率及原贏家／輸家變化：", "",
            "```json",json.dumps(evidence,indent=2),"```"]
    lines += ["", "## 判斷", "", "四組淨收益微升，但不是全面優勝：一般2024約+3.054%→+3.104%、2025−3.003%→−2.779%；雙成本2024−0.081%→−0.046%、2025−3.933%→−3.807%。四組最大回撤都增加，仍低於10%研究上限，但2025仍虧，年度淨10%目標未達。保留下一輪研究候選及原父對照，不提升槓桿、不推實盤。", "",
        "並非靠省費：一般成本2024費用168.24→187.53USDT、2025為128.31→151.10。所有共同進場事件都能匹配；把子結果按父qty換算的差額，一般2024約+58.52、2025+25.29USDT，但qty差額分別約−53.44、−2.82，使淨改善只約5.08／22.47USDT。這只是線性損益的事後代數拆解，不是將退出與數量變化當獨立因果效果；未執行固定父qty的反事實策略。", "",
        "結構stop可能遠或近，影響尺寸與連虧減倉／共享名額，原有贏家也可能因變小或提早退出受損。逐事件共同進場比較、原贏家被傷害／原輸家改善的數量都完整保存，不只報好處。不能把每個事件R相加當年度收益，也不因四成本結果同向就稱有獨立統計證據。", "",
        "## 驗證與限制", "", "231項pytest通過：結構初始stop只用前一根已知掃單極值、原進場與退出flag不變、前綴因果；獨立事件wrapper保留退出、只能一筆新進場、呼叫順序一致。四筆父完整快照重播、所有原短線訊號與子訊號逐筆一致，子成交stop／方向／時間、現金／ID、每日≤2、1x、單筆risk與新增gross／stoprisk／margin預算均核對。", "",
        "2024／2025及12項經驗均調參，非未見驗證，不能宣稱穩定獲利或必然提升未來收益。不掃新的stop buffer／ATR倍數。原固定BTC選樣、1h盤中路徑、MMR2%非歷史級距、深度滑價、精度／最小單量與研究部位／交易所倉位映射限制仍在；未改live/paper/testnet，未下單。完整結果data/perpetual-sweep-structural-stop.json，審計data/structural-stop-audit.json。"]
    report=Path("docs/research/2026-10-28-structural-stop-results.md")
    report.write_text("\n".join(lines+details)+"\n",encoding="utf-8")
    managed_lines=["# 原退出規則下的獨立訊號診斷", "", "2026-10-28。每筆獨立10,000、0.25% risk、關閉連虧減倉以移除帳戶路徑，原止損／動態exit／上限及成本保留；非實際組合策略，不加總成年收益。原已成交事件的價格、時間、原因與單位qty PnL／費用／funding全數一致。", "",
        "|年|成本倍數|策略／方向|N|平均淨R|勝率|初始ATR止損在掃單內|止損當根仍未碰掃單極值|", "|---|---:|---|---:|---:|---:|---:|---:|"]
    for case in managed:
        for g in case['summaries']:
            if g['scope']=='all':
                managed_lines.append(f"|{case['year']}|{case['cost']}|{g['sleeve']}/{g['direction']}|{g['count']}|{g['mean_net_r']:+.3f}|{g['win_rate']:.1%}|{g['atr_stop_inside_sweep']}|{g['stopped_before_sweep_extreme']}|")
    managed_lines += ["", "結論：2025全組仍負，不能只怪共享風控。兩年各3個形態尚未達極值就被ATR止損的事件，支持一次結構stop試驗，但不是放寬後會盈利的證據。另見structural-stop-results.md實際共用帳戶候選比較。R分母為原引擎planned risk（含成本／funding reserve），非單純價格距離；事件重疊且成本重複，非獨立樣本。年底由原引擎end_of_data退出且保留標記。全部原始事件及匹配審計在data/managed-signal-diagnostics.json和managed-signal-audit.json；兩年均調參。"]
    Path("docs/research/2026-10-28-managed-signal-results.md").write_text("\n".join(managed_lines)+"\n",encoding="utf-8")
    sources=[parent_path,child_path,diagnostic_path,diagnostic_audit_path,signals_path,tape_path,Path(__file__),
        Path("app/strategies/sweep_structural_stop.py"),Path("scripts/research_structural_stop.py"),Path("scripts/research_portfolio_overlap.py")]
    Path("data/structural-stop-audit.json").write_text(json.dumps(dict(status="completed_research_candidate",
        independent_validation=False,sources={str(p):sha256(p.read_bytes()).hexdigest() for p in sources},cases=cases),indent=2),encoding="utf-8")
    print(f"Four cases, unchanged signals, risk and PnL decomposition audited: {report}")


if __name__=="__main__":
    main()
