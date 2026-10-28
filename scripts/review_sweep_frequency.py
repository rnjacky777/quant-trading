"""Freeze the failed frequency experiment, including all costs and entry audits."""
from bisect import bisect_left
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.frequency import entry_frequency
from app.data.models import Candle
from app.strategies.sweep_window import DirectionalSweepWindowStrategy


def main() -> None:
    parent_path=Path("data/perpetual-confirmed-efficiency.json")
    child_path=Path("data/perpetual-sweep-frequency.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    rows=json.loads(child_path.read_text())['rows']
    assert len(rows)==4 and {(r['year'],r['cost_multiplier']) for r in rows}==set(parents)
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape]
    cases=[]
    lines=["# 短線頻率目標與三小時確認實驗結果", "", "2026-10-28。portfolio_confirmed_efficiency → portfolio_sweep_window。只改短線signal確認期限1根→最多3根1h；波段、出場及風控不變。全部父快照與指紋已在執行時逐一重播一致。", "",
        "## 結論", "", "未採用：增加交易卻令兩年一般及雙成本收益全部退步，回撤亦上升。保留父候選作研究參考，沒有宣稱父候選已可實盤獲利。兩年各10%／回撤10%仍未達成；不以加槓桿補足收益，不湊每日單量。", "",
        "短線有機會時每日1–2次的偏好已加入AGENTS.md與合約研究頁，顯示全年筆數、全年日均、短線日均、有進場天數、無進場天數及短線／波段多空分組。全年日均除以365／366，不以活躍日平均冒充每天頻率。共享每日最多2次仍涵蓋波段。", "",
        "## 全部期間與成本", "", "每年重設10,000USDT；一般單邊費10bps／滑價5bps，雙成本20bps／10bps；含實際funding，全部實際1x。", "",
        "|年|成本倍數|父收益|候選收益|父回撤|候選回撤|父短線筆數|候選短線筆數|候選總筆數|候選短線日均|",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    details=[]
    for row in rows:
        p=parents[(row['year'],row['cost_multiplier'])]
        assert row['status']==p['status']=='completed'
        for key in ('input_fingerprints','config','portfolio_limits'):
            assert row[key]==p[key]
        for new,old in zip(row['sleeves'],p['sleeves'],strict=True):
            assert new['name']==old['name'] and new['config']==old['config']
            if new['name']=='swing':
                assert new==old
        result=row['result']; trades=result['trades']; m=result['metrics']; pm=p['result']['metrics']
        f=entry_frequency(trades,row['year']); pf=entry_frequency(p['result']['trades'],row['year'])
        assert isclose(result['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert len({t['position_id'] for t in trades})==len(trades)
        assert all(t['leverage']==1 for t in trades)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        accepted=[a for a in result['admissions'] if a['status']=='accepted']
        assert {a['position_id'] for a in accepted}=={t['position_id'] for t in trades}
        for a in accepted:
            eq=a['equity_before']; limit=row['portfolio_limits']
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limit['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limit['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limit['max_margin_fraction'])+1e-7
        grouped=defaultdict(lambda:dict(count=0,pnl=0.))
        checked=0
        for t in trades:
            group=grouped[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"]
            group['count']+=1; group['pnl']+=t['pnl']
            if t['sleeve']=='intraday':
                index=bisect_left(times,t['entry_timestamp_ms'])
                signal=DirectionalSweepWindowStrategy().generate(tape[:index])
                assert signal.direction==t['direction']
                assert isclose(signal.stop_loss_price,t['stop_loss_price'],abs_tol=1e-8)
                assert signal.timestamp.timestamp()*1000==times[index]-3600000
                checked+=1
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{pm['total_return']:+.3%}|{m['total_return']:+.3%}|{pm['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{pf['intraday']}|{f['intraday']}|{f['total']}|{f['intraday_daily_average']:.3f}|")
        cases.append(dict(year=row['year'],cost=row['cost_multiplier'],checks='passed',
            intraday_signals_recomputed=checked,frequency=f,parent_frequency=pf,metrics=m,grouped=dict(grouped)))
        details += ["",f"## {row['year']}／成本{row['cost_multiplier']}倍完整證據","",
            "收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding：","",
            "```json",json.dumps(dict(metrics=m,frequency=f,grouped=dict(grouped)),indent=2),"```"]
    lines += ["", "## 為什麼不採用與後續假說", "",
        "原模式本身只出現82／98次合格掃單確認，波動門檻後63／44次；延長等待只提高到97／63筆實際短線，仍僅日均0.265／0.173，遠低於每天1次。新增訊號沒有帶來淨收益改善，不能透過持續放寬同一掃單形態來保證提高收益或頻率。新的訊號也會改變每日名額、風險與波段資金路徑，因此不能把全額變差只歸因手續費或新增交易。", "",
        "[TradingView官方策略文件](https://www.tradingview.com/pine-script-docs/concepts/strategies/#simulating-trading-costs)說明必須模型化佣金及滑價，忽略成本可能高估績效；此處全部沿用父成本並保留雙成本失敗。該文件不證明任何進場模式能獲利。", "",
        "下一個待驗證假說：若要接近每日機會，需要獨立、可重現的短線進場模型，而非只延長掃單。先用當時已完成的1h／4h資料建立趨勢回撤結束之機會事件與交易成本空間診斷，檢查同一事件重複與跨年穩定性；只有形成合理證據後，才單獨測試替換短線進場。尚未實作或宣稱此假說有優勢，不在本輪失敗後掃另一個等待根數。", "",
        "200項pytest通過；新增期限、失效、首次跨越、過期拒絕、多空與原即時確認一致性，以及UTC日曆分母／進場日／分組統計。逐筆短線用截至進場前資料重算，核對現金、ID、每日上限、1x及每次新增的gross／stoprisk／margin預算。2024／2025為調參證據，非未見驗證；同一期間成本實驗非獨立樣本。", "",
        "仍保留1h盤中路徑、固定MMR2%非歷史級距、精度／最小單量、深度滑價、虛擬獨立研究部位與真實交易所倉位映射等限制。沒有改live／paper／testnet或下單。全部曲線與交易保存在data/perpetual-sweep-frequency.json，儀表板標為未採用，父結果完整保留。"]
    report=Path("docs/research/2026-10-28-frequency-results.md")
    report.write_text("\n".join(lines+details)+"\n",encoding="utf-8")
    paths=[parent_path,child_path,tape_path,Path(__file__),Path("app/strategies/sweep_window.py"),
        Path("scripts/research_sweep_frequency.py"),Path("scripts/research_portfolio_overlap.py"),Path("app/backtest/frequency.py")]
    Path("data/sweep-frequency-audit.json").write_text(json.dumps(dict(status="completed_not_adopted",
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},cases=cases),indent=2),encoding="utf-8")
    print(f"Four cases and all short-horizon entries audited: {report}")


if __name__=="__main__":
    main()
