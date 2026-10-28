"""Audit a controlled exit change, including displaced winners and all costs."""
from bisect import bisect_left
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.frequency import entry_frequency


def main() -> None:
    parent_path=Path("data/perpetual-confirmed-efficiency.json")
    child_path=Path("data/perpetual-swing-protection.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    rows=json.loads(child_path.read_text())['rows']
    assert len(rows)==4 and {(r['year'],r['cost_multiplier']) for r in rows}==set(parents)
    tape=json.loads(tape_path.read_text());times=[int(c['open_time']) for c in tape]
    cases=[];details=[]
    lines=["# 研究總結、波段價格保護優化與收益核對", "", "2026-10-28。已讀10項研究經驗（含本次），主流程仍保留原掃單＋波段確認／效率候選portfolio_confirmed_efficiency。尚無每年10%淨收益／回撤≤10%的可推薦版本。", "",
        "## 之前經驗總結", "", "增加頻率、延長持有、空單去重均未建立穩定正期望。2025原候選未扣費與funding的成交價差已負，不是只有成本問題。短線30筆虧損沒有完成收盤到過+1R，故本次不給短線加移動保護；波段29筆虧損有6筆曾到+1R，足以支持一次波段exit試驗，但不能先推定盈利。", "",
        "## 唯一修改", "", "portfolio_confirmed_efficiency → portfolio_swing_protection。只對波段：完成1h收盤達初始價格風險+1R，收盤後把止損提高／降低至成交價，下一根才生效；多空對稱、止損不放寬。初始止損、原訊號及退出、24h短線／168h波段、風險及成本均不變，無新增槓桿。價格保本≠淨保本，跳空仍按開盤價、費用滑價與funding照算。", "",
        "## 全部期間／成本收益", "", "每年本金10,000 USDT，一般單邊費10bps／滑價5bps，雙成本20bps／10bps，另含實際funding；全部實際1x。四筆父完整快照和行情／mark／funding指紋均逐一重播一致，再執行子候選，沒有刪除不利案例。", "",
        "|年|成本倍數|父淨收益|候選淨收益|收益差（百分點）|父最大回撤|候選最大回撤|交易數|", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        parent=parents[(row['year'],row['cost_multiplier'])]
        assert row['status']==parent['status']=='completed'
        for key in ('config','portfolio_limits','sleeves','input_fingerprints'):
            assert row[key]==parent[key]
        assert row['swing_price_protection']==dict(activation_r=1.0,stop="entry_price",effective="next_hour")
        result=row['result'];trades=result['trades'];m=result['metrics'];pm=parent['result']['metrics']
        assert isclose(result['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert len({t['position_id'] for t in trades})==len(trades)
        assert all(t['leverage']==1 for t in trades)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        accepted={a['position_id']:a for a in result['admissions'] if a['status']=='accepted'}
        assert set(accepted)=={t['position_id'] for t in trades}
        for a in accepted.values():
            eq=a['equity_before'];limits=row['portfolio_limits']
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
        grouped=defaultdict(lambda:dict(count=0,pnl=0.));updates_checked=0;paired=[]
        parent_events={(t['sleeve'],t['direction'],t['entry_timestamp_ms']):t for t in parent['result']['trades']}
        for t in trades:
            g=grouped[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"]
            g['count']+=1;g['pnl']+=t['pnl']
            updates=accepted[t['position_id']].get('stop_updates',[])
            assert len(updates)<=1
            if t['sleeve']!='swing':
                assert not updates and t['exit_reason']!='profit_protection'
            for update in updates:
                assert t['sleeve']=='swing'
                assert update['initial_stop']==t['stop_loss_price']==update['from_stop']
                assert update['to_stop']==t['entry_price']
                assert t['direction']*(update['to_stop']-update['from_stop'])>0
                index=bisect_left(times,update['decision_timestamp_ms'])
                assert times[index]==update['decision_timestamp_ms']
                assert float(tape[index]['close'])==update['trigger_close']
                assert t['direction']*(update['trigger_close']-t['entry_price'])>=abs(t['entry_price']-t['stop_loss_price'])
                assert update['decision_timestamp_ms']>=t['entry_timestamp_ms']
                assert update['active_from_ms']==update['decision_timestamp_ms']+3600000
                updates_checked+=1
            if t['exit_reason']=='profit_protection':
                assert updates and t['exit_timestamp_ms']>=updates[0]['active_from_ms']
                event=(t['sleeve'],t['direction'],t['entry_timestamp_ms'])
                if event in parent_events:
                    p=parent_events[event]
                    paired.append(dict(parent_position_id=p['position_id'],child_position_id=t['position_id'],
                        parent_pnl=p['pnl'],child_pnl=t['pnl'],parent_exit=p['exit_reason'],child_exit=t['exit_reason']))
        opportunity_cost=dict(common_protected_events=len(paired),
            parent_winners=sum(p['parent_pnl']>0 for p in paired),parent_losers=sum(p['parent_pnl']<0 for p in paired),
            parent_pnl=sum(p['parent_pnl'] for p in paired),child_pnl=sum(p['child_pnl'] for p in paired),events=paired)
        f=entry_frequency(trades,row['year'])
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{pm['total_return']:+.3%}|{m['total_return']:+.3%}|{(m['total_return']-pm['total_return'])*100:+.3f}|{pm['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|")
        evidence=dict(year=row['year'],cost=row['cost_multiplier'],checks="passed",metrics=m,frequency=f,
            grouped=dict(grouped),stop_updates_checked=updates_checked,common_event_comparison=opportunity_cost)
        cases.append(evidence)
        details += ["",f"## {row['year']}／成本{row['cost_multiplier']}倍完整指標及代價", "",
            "收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率及共同進場事件對照：", "",
            "```json",json.dumps(evidence,indent=2),"```"]
    lines += ["", "## 驗證判斷", "", "只有部分提升：2025一般成本由−3.003%改善至−2.743%，雙成本由−3.933%改善至−3.681%；2024一般成本由+3.054%退步至+2.238%，雙成本由−0.081%退步至−0.293%，兩種成本的回撤亦較父版本大。因此本候選未採用為替代，不宣稱整體提升或解決虧損，仍保留父版本研究參考。", "",
        "一般成本共同進場事件中，2024有4筆父版本原贏家被保護退出，另5筆父原輸家也走保護退出；2025為1筆父原贏家、6筆父原輸家。這是匹配同策略／方向／進場時間的描述比較，不是獨立因果估計：共享風險釋放、名額、數量與funding路徑都可改變，亦有子新單找不到同事件父單，不拿未匹配事件強行比較。", "",
        "## 可信範圍", "", "216項pytest通過。新增多空對稱、完成close後下一根生效、當根先觸及高低不追溯保護、wick不觸發、跳空可虧、初始止損保存、短線不受影響；四筆父快照逐一完整重播即驗證預設關閉行為不變。審計逐筆保護trigger close／1R／生效時間，並核對cash/PnL、ID、每日≤2、全部1x、新增gross／stoprisk／margin預算及費率完全一致。", "",
        "這是同資料可重現比較，不是未見資料驗證。2024／2025已用於調參，10項策略選擇也造成多重嘗試風險；不能合併成本重複樣本或挑盈利月份。每年10%目標與頻率偏好都未被證明可同時達成。", "",
        "原有固定BTC選樣、1h盤中路徑、固定MMR2%非歷史級距、滑價／深度、精度／最小單量、虛擬多筆部位與交易所倉位映射限制仍在。此出場僅在研究引擎實作，沒有宣稱paper/testnet/live可交易支援，未改交易設定或下單。結果data/perpetual-swing-protection.json，審計data/swing-protection-audit.json；已加入第10項研究經驗。"]
    report=Path("docs/research/2026-10-28-optimization-verification.md")
    report.write_text("\n".join(lines+details)+"\n",encoding="utf-8")
    sources=[parent_path,child_path,tape_path,Path(__file__),Path("app/backtest/portfolio_research.py"),
        Path("scripts/research_swing_protection.py"),Path("scripts/research_portfolio_overlap.py")]
    Path("data/swing-protection-audit.json").write_text(json.dumps(dict(status="completed_mixed_not_adopted",
        independent_validation=False,sources={str(p):sha256(p.read_bytes()).hexdigest() for p in sources},cases=cases),indent=2),encoding="utf-8")
    print(f"Four periods/costs and all stop updates audited; report: {report}")


if __name__=="__main__":
    main()
