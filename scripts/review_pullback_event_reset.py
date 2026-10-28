"""All-period audit of the reset child, with honest parent and reference comparisons."""
from bisect import bisect_left
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.frequency import entry_frequency
from app.data.models import Candle
from app.strategies.pullback_reset import DirectionalPullbackResetStrategy


def main() -> None:
    parent_path=Path("data/perpetual-directional-pullback.json")
    child_path=Path("data/perpetual-pullback-reset.json")
    reference_path=Path("data/perpetual-confirmed-efficiency.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    references={(r['year'],r['cost_multiplier']):r for r in json.loads(reference_path.read_text())['rows']}
    rows=json.loads(child_path.read_text())['rows']
    assert len(rows)==4 and {(r['year'],r['cost_multiplier']) for r in rows}==set(parents)
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[];details=[]
    lines=["# 回撤空單事件重置：部分問題得到改善，仍未獲利", "",
        "2026-10-28。portfolio_directional_pullback → portfolio_pullback_reset。單項signal改動：重置後第一個合格空單才允許；必須完成1h向上越過當時完成4h SMA20才重新武裝。多單、波段、止損、24h上限、風險、費率與funding完全不變。設計事先保存於2026-10-28-pullback-reset-design.md。", "",
        "## 全部四筆比較", "", "每年本金10,000USDT，一般單邊費10bps／滑價5bps，雙成本20bps／10bps，另含實際funding，實際全部1x。父全部四筆資料指紋與完整快照已逐一重播一致。", "",
        "|年|成本倍數|失敗回撤父收益|事件重置收益|重置回撤|總筆數|短線筆數|原掃單參考收益|", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        key=(row['year'],row['cost_multiplier']);parent=parents[key];ref=references[key]
        assert row['status']==parent['status']=='completed'
        for field in ('input_fingerprints','config','portfolio_limits'):
            assert row[field]==parent[field]
        assert row['input_fingerprints']==ref['input_fingerprints']
        for new,old in zip(row['sleeves'],parent['sleeves'],strict=True):
            assert new['name']==old['name'] and new['config']==old['config']
            if new['name']=='swing':
                assert new==old
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
        start=1704067200000 if row['year']==2024 else 1735689600000
        warmup_index=bisect_left(times,start-243*3600000)
        grouped=defaultdict(lambda:dict(count=0,pnl=0.));checked=0
        for t in trades:
            g=grouped[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"]
            g['count']+=1;g['pnl']+=t['pnl']
            if t['sleeve']=='intraday':
                index=bisect_left(times,t['entry_timestamp_ms'])
                signal=DirectionalPullbackResetStrategy().generate(tape[warmup_index:index])
                assert signal.direction==t['direction']
                assert signal.timestamp.timestamp()*1000==times[index]-3600000
                assert isclose(signal.stop_loss_price,t['stop_loss_price'],abs_tol=1e-8)
                checked+=1
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{pm['total_return']:+.3%}|{m['total_return']:+.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|{f['intraday']}|{ref['result']['metrics']['total_return']:+.3%}|")
        evidence=dict(year=row['year'],cost=row['cost_multiplier'],checks="passed",metrics=m,frequency=f,
            grouped=dict(grouped),intraday_entries_recomputed=checked,
            executed_price_pnl_before_fees_funding=sum(t['pnl']+t['fees']-t['funding'] for t in trades))
        cases.append(evidence)
        details += ["",f"## {row['year']}／成本{row['cost_multiplier']}倍完整指標", "",
            "收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：", "",
            "```json",json.dumps(evidence,indent=2),"```"]
    lines += ["", "## 決策", "",
        "四組均改善失敗回撤父候選的淨收益與回撤，但都仍虧，且每組都不如原掃單參考portfolio_confirmed_efficiency。未採用、不提升槓桿、不宣稱已解決負期望；首次進場組原本也虧，去重只能處理部分問題。收益差也受到共享每日名額／資金路徑影響，不能將全部改善直接歸因被移除空單的因果效果。", "",
        "當前空單事件會在原合格Signal發出時消耗，即便當時風控拒絕成交也不補發，這是可在策略層重現的明確選擇。沒有硬性單持倉限制，新重置可在舊部位仍存在時允許新Signal。未觀察到完整重置或暖機不足時保守不發空單；逐筆審計使用相同243h暖機，沒有偷偷追加更早行情。", "",
        "## 後續研究判斷與限制", "",
        "不在本輪接著掃重置均線長度或冷卻時數。下一步應先固定現有候選，檢查各自逐月扣成本期望與訊號後路徑，形成能否放棄這個回撤進場家族的判斷；不能因相較一個很差的父版本改善，就替換較好的原掃單參考或宣稱有可交易優勢。", "",
        "參考作者原文[The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)：反覆在相同資料測試策略有多重嘗試及過擬合問題。因此保留所有失敗，不宣稱本專案已計算PBO或取得獨立統計驗證。2024／2025皆調參，並非未見驗證；成本案例／重疊分組不能加總為獨立樣本。", "",
        "206項pytest通過，新增第一個空單、無新重置拒絕重複、重新跨越後允許、多單及退出不變、無成交依賴、歷史重放與呼叫順序一致；逐筆全部短線進場用相同暖機的完成歷史重算方向／時間／止損。核對現金、ID、每日≤2、1x與新增部位gross／stoprisk／margin。完整曲線與交易存data/perpetual-pullback-reset.json，儀表板標未採用。", "",
        "仍有固定BTC選樣、1h盤中路徑、MMR2%非歷史級距、下單精度／最小單量、深度滑價與虛擬部位和交易所倉位映射限制；進場比例不是永久持倉上限。未改live/paper/testnet或下單。"]
    report=Path("docs/research/2026-10-28-pullback-reset-results.md")
    report.write_text("\n".join(lines+details)+"\n",encoding="utf-8")
    paths=[parent_path,child_path,reference_path,tape_path,Path(__file__),Path("app/strategies/pullback_reset.py"),
           Path("scripts/research_pullback_reset.py"),Path("scripts/research_portfolio_overlap.py")]
    Path("data/pullback-event-reset-audit.json").write_text(json.dumps(dict(status="completed_not_adopted",
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},cases=cases),indent=2),encoding="utf-8")
    print(f"All four cases and each intraday decision audited: {report}")


if __name__=="__main__":
    main()
