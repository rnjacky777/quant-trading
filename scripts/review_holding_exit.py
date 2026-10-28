"""Audit unchanged signals/costs, diagnose negative price edge and reject 48h."""
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.frequency import entry_frequency


def main() -> None:
    parent_path=Path("data/perpetual-confirmed-efficiency.json")
    child_path=Path("data/perpetual-holding-exit.json")
    diagnostic_path=Path("data/profit-failure-diagnostics.json")
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    rows=json.loads(child_path.read_text())['rows']
    assert len(rows)==4 and {(r['year'],r['cost_multiplier']) for r in rows}==set(parents)
    cases=[];details=[]
    lines=["# 淨收益不足的問題診斷與48h出場實驗", "", "2026-10-28。使用者要求先找問題、改善淨收益，而非增加成本。沿用portfolio_confirmed_efficiency，不採已失敗的放寬確認／回撤進場。父四筆指紋與完整快照逐一重播一致。", "",
        "## 核心診斷", "", "1. 負收益不是只有費用問題。成交價差損益=pnl+fees−funding，仍包含實際執行滑價，不是假設零成本重跑。2025原候選價差−166.73USDT、手續費128.31、funding−5.29，淨−300.34；回撤模型2024價差−180.49、費421.34、funding−43.49，淨−645.32；2025價差−229.85、費303.80、funding−5.48，淨−539.13。不能把負價差歸因佣金或透過降低設定美化。", "",
        "2. 勝率與平均盈虧配比不足。2025原候選淨勝率30.59%、平均贏18.17／平均虧13.10USDT，依該樣本需約41.89%才損益兩平；2024勝率38.61%、樣本平衡勝率32.18%，故仍正收益。這是已實現樣本恆等式，不是預測未來需要固定勝率。回撤模型2024勝率28.90%、樣本平衡35.90%；2025勝率33.15%、樣本平衡43.76%，顯示不只是增加交易就能改善。", "",
        "3. 重複事件有方向差異。回撤模型同一段4h SMA20/60方向內，後續短線多單2024為114筆−565.57、2025為37筆+93.64；後續短線空單2024為73筆−223.11、2025為69筆−287.31。首次進場組也虧，不能只靠去重保證盈利。原候選2025後續短線空單反而14筆+14.39，故不能將失敗回撤模型的規則直接套到原候選。重複不一定同時持有，不取消多部位能力。", "",
        "4. 出場與進場品質須分開測。原候選短線24h到期組2024淨+521.28、2025+187.33，但其餘退出組淨虧，故提出延長一個完整交易日的單項exit假說；此分組非延長一定有效的證據。", "",
        "全部原候選及回撤模型、2024／2025、一般／雙成本、各策略方向／首次重複／出場的數據保存data/profit-failure-diagnostics.json。重複分組使用當時完成4h均線方向，沒有用未來行情；同一成本和分組不當獨立樣本加總。", "",
        "## 單項修改結果", "", "portfolio_confirmed_efficiency → portfolio_holding_48h：只改短週期最大持有24→48h，所有進場／止損／訊號退出／波段／風控／成本不變。一般費10bps／滑價5bps，雙成本20bps／10bps，含實際funding；年度本金10,000，實際1x。", "",
        "|年|成本倍數|父收益|48h收益|父回撤|48h回撤|交易數|短週期筆數|", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        parent=parents[(row['year'],row['cost_multiplier'])]
        assert row['status']==parent['status']=='completed'
        assert row['input_fingerprints']==parent['input_fingerprints']
        assert row['portfolio_limits']==parent['portfolio_limits']
        expected=dict(parent['config'],holding_hours=48)
        assert row['config']==expected
        for new,old in zip(row['sleeves'],parent['sleeves'],strict=True):
            assert new['name']==old['name'] and new['strategy']==old['strategy']
            assert new['config']==(dict(old['config'],holding_hours=48) if new['name']=='intraday' else old['config'])
        result=row['result'];trades=result['trades'];m=result['metrics'];pm=parent['result']['metrics']
        f=entry_frequency(trades,row['year'])
        assert isclose(result['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert len({t['position_id'] for t in trades})==len(trades)
        assert all(t['leverage']==1 for t in trades)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        accepted=[a for a in result['admissions'] if a['status']=='accepted']
        assert {a['position_id'] for a in accepted}=={t['position_id'] for t in trades}
        for a in accepted:
            eq=a['equity_before'];limits=row['portfolio_limits']
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
        grouped=defaultdict(lambda:dict(count=0,pnl=0.))
        for t in trades:
            group=grouped[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"]
            group['count']+=1;group['pnl']+=t['pnl']
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{pm['total_return']:+.3%}|{m['total_return']:+.3%}|{pm['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|{f['intraday']}|")
        evidence=dict(year=row['year'],cost=row['cost_multiplier'],checks="passed",metrics=m,frequency=f,
            grouped=dict(grouped),executed_price_pnl_before_fees_funding=sum(t['pnl']+t['fees']-t['funding'] for t in trades))
        cases.append(evidence)
        details += ["",f"## {row['year']}／成本{row['cost_multiplier']}倍完整指標", "",
            "收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：", "",
            "```json",json.dumps(evidence,indent=2),"```"]
    lines += ["", "## 決策與限制", "", "不採用48h：四筆成本情境收益全部比父候選差，不能說提高了淨收益；延長持有假說被本次歷史結果反駁。固定止損、訊號反向與時間上限的組合沒有因延長而改善，應回到事件品質，不再掃36／60／72小時直到數字好看。沒有降低費率或加槓桿。", "",
        "下一個可辯護研究方向是先驗證『回撤模型的重複空頭恢復事件是否應先等待結構失效後重置』，但首次組也虧，且原掃單空單不同，因此需先定義能在當時觀察的事件並保留失敗跨年證據，不能直接禁止所有空單或所有同向多部位。本輪只執行上述一個exit候選，不把待驗證方向宣稱已提升收益。", "",
        "204項pytest通過；新增真實引擎持有24／48h邊界及48h仍可訊號／止損提早退出。審計核對四筆輸入、僅holding變更、策略名稱和費率完全不變、現金／ID／每日上限／1x，以及每次進場gross／stoprisk／保證金上限；後續市場變動仍可能造成比例漂移。", "",
        "2024／2025均為調參非未見資料，沒有泛化盈利證據。固定BTC選樣、1h盤中路徑、MMR2%非歷史級距、下單精度／最小單量、深度滑價、獨立研究部位與真實交易所倉位映射限制仍在。全部曲線交易存data/perpetual-holding-exit.json，儀表板標未採用並顯示各策略最長持有。未改live/paper/testnet或下單。"]
    report=Path("docs/research/2026-10-28-profit-diagnosis-results.md")
    report.write_text("\n".join(lines+details)+"\n",encoding="utf-8")
    paths=[parent_path,child_path,diagnostic_path,Path(__file__),Path("scripts/research_holding_exit.py"),Path("scripts/research_portfolio_overlap.py")]
    Path("data/holding-exit-audit.json").write_text(json.dumps(dict(status="completed_not_adopted",
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},cases=cases),indent=2),encoding="utf-8")
    print(f"Audited four cases and unchanged costs/signals: {report}")


if __name__=="__main__":
    main()
