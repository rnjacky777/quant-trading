"""Fixed-bin exploratory diagnostics; no threshold search or new backtest."""
from bisect import bisect_left
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

from app.backtest.entry_context import entry_context
from app.backtest.signal_diagnostics import HORIZONS, summarize_signals
from app.data.models import Candle


def main() -> None:
    source=Path("data/all-signal-diagnostics.json")
    audit_path=Path("data/all-signal-audit.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    original=json.loads(source.read_text())
    audit=json.loads(audit_path.read_text())
    if len(original['cases'])!=4 or not all(c['full_snapshot_equal'] for c in audit['cases']):
        raise ValueError("four replayed cases required")
    for path,digest in audit['sources'].items():
        if sha256(Path(path).read_bytes()).hexdigest()!=digest:
            raise ValueError(f"original diagnostic provenance changed: {path}")
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape]
    cases=[]
    lines=["# 訊號入場延伸與開盤價差診斷", "", "2026-10-28。固定原全部訊號，不改策略。四筆正常／雙成本資料均保留，原完整快照重播審計及來源SHA256先核對；本輪沒有另跑改動策略。", "",
        "延伸＝direction×(signal close−當時完成4h SMA20)/完成4h ATR14。分組是事前記錄的自然整數ATR單位，不是最佳化門檻。開盤gap在執行時才知道，不能回填成事前特徵。以下都是固定窗口事件淨變化，沒有原止損／強平／動態出場／資金限制，不是策略年收益。", "",
        "## 一般成本24h分組速覽", "", "|年|策略／方向|特徵|固定分組|N|24h均值|中位數|非重疊N|非重疊均值|", "|---|---|---|---|---:|---:|---:|---:|---:|"]
    gap_rows=[]
    for case in original['cases']:
        year=case['year'];start=1704067200000 if year==2024 else 1735689600000
        warmup=bisect_left(times,start-243*3600000)
        events=[];groups=defaultdict(list)
        for event in case['signals']:
            i=bisect_left(times,event['timestamp_ms'])
            if times[i]!=event['timestamp_ms']:
                raise ValueError("missing execution bar")
            context=entry_context(tape[warmup:i],event['direction'],tape[i].open)
            enriched=dict(event,entry_context=context)
            events.append(enriched)
            groups[('extension',context['extension_bucket'])].append(enriched)
            groups[('gap',context['gap_bucket'])].append(enriched)
        summaries=[]
        for (kind,bucket),items in sorted(groups.items()):
            for stat in summarize_signals(items):
                if stat['scope']!='all':
                    continue
                record=dict(stat,feature=kind,bucket=bucket)
                summaries.append(record)
                if case['cost']==1 and stat['hours']==24:
                    label=('短線' if stat['sleeve']=='intraday' else '波段')+('多' if stat['direction']==1 else '空')
                    def pct(value):
                        return '—' if value is None else f"{value:+.3%}"
                    lines.append(f"|{year}|{label}|{kind}|{bucket}|{stat['observed_count']}|{pct(stat['mean_net_return'])}|{pct(stat['median_net_return'])}|{stat['nonoverlap_count']}|{pct(stat['nonoverlap_mean_net'])}|")
                    print(year,label,kind,bucket,'N',stat['observed_count'],'net24',round(stat['mean_net_return']*100,3) if stat['mean_net_return'] is not None else None)
        gap_stats=[]
        for sleeve in ('intraday','swing'):
            for side in (1,-1):
                gaps=[abs(e['entry_context']['execution_gap_bps']) for e in events if e['sleeve']==sleeve and e['direction']==side]
                stat=dict(sleeve=sleeve,direction=side,count=len(gaps),median_abs_bps=median(gaps) if gaps else None,
                          maximum_abs_bps=max(gaps) if gaps else None)
                gap_stats.append(stat)
                if case['cost']==1 and gaps:
                    gap_rows.append(f"|{year}|{sleeve}/{side}|{len(gaps)}|{median(gaps):.4f}|{max(gaps):.4f}|5|")
        cases.append(dict(year=year,cost=case['cost'],actual_portfolio_metrics=case['actual_portfolio_metrics'],
                          summaries=summaries,gap_stats=gap_stats,signals=events))
    lines += ["", "## 開盤gap的經濟幅度", "", "絕對gap大小僅指下一根open與前close之差，不等於實際交易深度或滑價；既定單邊滑價另外計算。", "",
        "|年|策略／方向|N|絕對gap中位數bps|最大bps|原滑價bps|", "|---|---|---:|---:|---:|---:|", *gap_rows,
        "", "## 解讀限制", "", "全部4／12／24h、正常與雙成本、樣本數／日數／截尾／非重疊敏感度及逐筆當時特徵保存在data/entry-extension-diagnostics.json。正常與雙成本共用同一批訊號，不是額外獨立證據。特徵兩種分組彼此重疊，不相加。", "",
        "沒有自動挑最佳門檻，沒有把某格均值正就稱有獲利策略；2024／2025都是已看過的調參資料，沒有未見驗證。價格延伸與未來變化是相關分組，不是因果實驗；固定窗口忽略止損／資金路徑，任何後續候選仍須原全期間與成本風控回測。小N結果不下定論。策略、成本、風險、槓桿和live/paper/testnet設定完全未變，未下單。"]
    report=Path("docs/research/2026-10-28-entry-extension-results.md")
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")
    paths=[source,audit_path,tape_path,Path(__file__),Path("app/backtest/entry_context.py")]
    Path("data/entry-extension-diagnostics.json").write_text(json.dumps(dict(
        used_for_tuning=True,independent_validation=False,is_executable_portfolio_return=False,
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},cases=cases),allow_nan=False),encoding="utf-8")
    print(f"Saved fixed-bin diagnostics for {len(cases)} cases: {report}")


if __name__=="__main__":
    main()
