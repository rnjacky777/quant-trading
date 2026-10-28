"""Audit the mean guard and explain why event averages did not translate."""
from bisect import bisect_left
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.frequency import entry_frequency
from app.data.models import Candle
from app.strategies.sweep_mean_guard import DirectionalSweepMeanGuardStrategy


def main() -> None:
    parent_path=Path("data/perpetual-confirmed-efficiency.json")
    child_path=Path("data/perpetual-sweep-mean-guard.json")
    context_path=Path("data/entry-extension-diagnostics.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    contexts={(r['year'],r['cost']):r for r in json.loads(context_path.read_text())['cases']}
    rows=json.loads(child_path.read_text())['rows']
    assert len(rows)==4 and {(r['year'],r['cost_multiplier']) for r in rows}==set(parents)
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[];details=[]
    lines=["# 進場延伸診斷與短線空單位置限制：實際回測", "", "2026-10-28。固定原候選portfolio_confirmed_efficiency，先完成全訊號延伸／gap分組，再事前記錄單項signal候選portfolio_sweep_mean_guard。不是重新調整已失敗的SMA回撤模型。", "",
        "## 診斷結果", "", "2025各策略方向的開盤gap絕對中位數約0.009bps，最大約0.235bps，遠低於既定單邊5bps滑價。不是以此否定真實滑價／深度，而是目前bar-close到next-open的價格差沒有足夠經濟幅度支持先改gap限制。", "",
        "波段2024多單45次全在>2個4h ATR仍有正24h事件均值，不能將2ATR上限套用全部策略。2025低延伸波多僅2筆，樣本不足。短線空單位於4h SMA20上方時，12／24h分組均值兩年較佳，但4h不一致且2025保留組24h仍負。因此只支持一次探索，不是已找到正期望或統計顯著優勢。所有窗口與正常／雙成本資料在data/entry-extension-diagnostics.json及entry-extension-results.md。", "",
        "## 唯一候選與全期間結果", "", "短線原掃單空單只在完成close≥當時完成4h SMA20時准入；多單、波段、止損、退出、費用、槓桿、共享風控全部不變。父四筆完整快照及指紋逐一重播一致才執行候選。每年10,000USDT，一般單邊費10bps／滑價5bps，雙成本20bps／10bps，含實際funding，全部實際1x。", "",
        "|年|成本倍數|父收益|候選收益|父回撤|候選回撤|總交易數|短線筆數|", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        key=(row['year'],row['cost_multiplier']);parent=parents[key]
        assert row['status']==parent['status']=='completed'
        for field in ('input_fingerprints','config','portfolio_limits'):
            assert row[field]==parent[field]
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
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
        start=1704067200000 if row['year']==2024 else 1735689600000
        warmup=bisect_left(times,start-243*3600000)
        grouped=defaultdict(lambda:dict(count=0,pnl=0.));checked=0
        for t in trades:
            g=grouped[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"]
            g['count']+=1;g['pnl']+=t['pnl']
            if t['sleeve']=='intraday':
                index=bisect_left(times,t['entry_timestamp_ms'])
                signal=DirectionalSweepMeanGuardStrategy().generate(tape[warmup:index])
                assert signal.direction==t['direction']
                assert isclose(signal.stop_loss_price,t['stop_loss_price'],abs_tol=1e-8)
                assert signal.timestamp.timestamp()*1000==times[index]-3600000
                checked+=1
        source_events={(e['timestamp_ms'],e['sleeve'],e['direction']):e for e in contexts[key]['signals']}
        excluded=[]
        for t in parent['result']['trades']:
            if t['sleeve']=='intraday' and t['direction']==-1:
                e=source_events[(t['entry_timestamp_ms'],t['sleeve'],t['direction'])]
                if e['entry_context']['signed_extension_4h_atr']>0:
                    excluded.append(dict(position_id=t['position_id'],pnl=t['pnl'],exit_reason=t['exit_reason']))
        f=entry_frequency(trades,row['year'])
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{pm['total_return']:+.3%}|{m['total_return']:+.3%}|{pm['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|{f['intraday']}|")
        price=sum(t['pnl']+t['fees']-t['funding'] for t in trades)
        parent_price=sum(t['pnl']+t['fees']-t['funding'] for t in parent['result']['trades'])
        evidence=dict(year=row['year'],cost=row['cost_multiplier'],checks="passed",metrics=m,frequency=f,
            grouped=dict(grouped),intraday_entries_recomputed=checked,
            parent_fill_price_pnl_before_fees_funding=parent_price,child_fill_price_pnl_before_fees_funding=price,
            excluded_parent_short_events=dict(count=len(excluded),winners=sum(e['pnl']>0 for e in excluded),
                net_pnl=sum(e['pnl'] for e in excluded),events=excluded))
        cases.append(evidence)
        details += ["",f"## {row['year']}／成本{row['cost_multiplier']}倍完整指標與排除代價", "",
            "收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率與逐筆排除對照：", "",
            "```json",json.dumps(evidence,indent=2),"```"]
    lines += ["", "## 是否提升收益", "", "沒有穩定提升：2024一般成本+3.054%→+2.905%、雙成本−0.081%→−0.092%；2025一般成本−3.003%→−3.399%，只有雙成本−3.933%→−3.888%微升。候選未採用，原候選仍保留研究參考；10%年目標未達，不升槓桿。", "",
        "為何分組看似較好，實際卻退步：固定24h均值沒有原止損及動態退出。2024被排除4筆父短空有2贏、合計原本+14.79USDT；2025排除17筆有5贏、合計−15.06，並非可直接視為大額虧損機會。原止損會截斷後續價格路徑，事件24h負不等於實際交易負。刪除事件也改變短線多空共用的連虧減倉、波段名額與風險路徑，不能拿凍結父交易直接相減當候選收益。", "",
        "2025一般成本實際總費用下降，成交價差損益（仍含滑價、未扣費／funding）卻由約−166.73變成−230.93USDT，顯示不是只要省費就能提高淨收益。頻率亦下降，不能聲稱此候選滿足每日1–2次偏好。", "",
        "## 保存及決策", "", "228項pytest通過；新增完成4h均線／ATR不讀未完成bar、自然分組邊界、短空均線相等准入、多單／退出不變。四筆父完整快照重播、候選所有短線進場從相同暖機重算方向／時間／止損，並核對cash/PnL、ID、每日≤2、1x與新增gross／stoprisk／margin。結果data/perpetual-sweep-mean-guard.json，審計data/sweep-mean-guard-audit.json，已列第11項研究經驗。", "",
        "本輪停止，不繼續掃1ATR、2ATR或小數距離直到數字變好。後續應把候選入場事件的原止損／動態退出路徑一併納入評估，再形成新的假說；先明確哪些訊號真的產生負期望，不只依固定時間均值分組。這不是新交易規則，也不保證可解決損失。", "",
        "2024／2025及分組已調參，非未見驗證；成本重複／重疊訊號非獨立樣本。仍有固定BTC選樣、1h盤中路徑、固定MMR2%非歷史級距、精度／最小量、深度滑價與虛擬多筆部位到交易所模式的限制。未改live/paper/testnet、未下單。"]
    report=Path("docs/research/2026-10-28-mean-guard-verification.md")
    report.write_text("\n".join(lines+details)+"\n",encoding="utf-8")
    paths=[parent_path,child_path,context_path,tape_path,Path(__file__),Path("app/strategies/sweep_mean_guard.py"),
        Path("scripts/research_sweep_mean_guard.py"),Path("scripts/research_portfolio_overlap.py")]
    Path("data/sweep-mean-guard-audit.json").write_text(json.dumps(dict(status="completed_not_adopted",
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},cases=cases),indent=2),encoding="utf-8")
    print(f"Four cases, entry guards and shared budgets audited: {report}")


if __name__=="__main__":
    main()
