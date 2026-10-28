"""Freeze experience and monthly/path diagnostics without tuning a new strategy."""
from bisect import bisect_left
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.lessons import research_lessons
from app.backtest.path_diagnostics import completed_close_path, monthly_equity
from app.data.models import Candle


def main(*, ledger_only: bool = False) -> None:
    root=Path("data")
    experience=research_lessons(root)
    (root/"research-experience.json").write_text(json.dumps(experience,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# 研究經驗：先查證據，再提出下一項變更", "", "2026-10-28。這是既有實驗的研究記憶，不是新策略版本、不會自動調參或交易。2024／2025都是調參資料，並非未見驗證。每項保留正常及雙成本全部四筆，不把重疊案例當獨立樣本。", "",
        "查閱：`python -m scripts.optimize_backtest lessons`。資料來源SHA256、父子及全部指標在data/research-experience.json。此指令只核對保存快照，不能取代原優化流程的資料與引擎重播。", "",
        "## 使用方式", "", "提出新假說前，先指出適用經驗、原先失敗原因、這次有何新證據及唯一變更。不要重做相同失敗方案，或把回撤空單結果直接套到掃單／多單。沒有可辯護變更就記錄不變更，不靠增加版本、放寬成本或槓桿追收益。保留年度淨收益／回撤及短線頻率三者，不強制湊筆數。", ""]
    for lesson in experience['lessons']:
        lines += [f"## {lesson['id']}：{lesson['parent']} → {lesson['child']}", "",
            f"假說：{lesson['hypothesis']}。", "", f"唯一變更：{lesson['one_change']}。", "",
            f"判斷：**{lesson['decision']}**。限制：{lesson['limitation']}。", "",
            "|年|成本倍數|父收益|子收益|子最大回撤|", "|---|---:|---:|---:|---:|"]
        for c in lesson['comparisons']:
            p,m=c['parent_metrics'],c['child_metrics']
            lines.append(f"|{c['year']}|{c['cost']}|{p['total_return']:+.3%}|{m['total_return']:+.3%}|{m['maximum_drawdown']:.3%}|")
        lines.append("")
    report=Path("docs/research/2026-10-28-research-experience.md")
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")
    if ledger_only:
        print(f"Updated {len(experience['lessons'])} evidence-linked lessons; diagnostics/decisions unchanged.")
        return
    tape_path=root/"btc-perpetual-1h/klines.json"
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape]
    files=("perpetual-confirmed-efficiency.json","perpetual-directional-pullback.json","perpetual-pullback-reset.json")
    cases=[]
    summary=["# 逐月淨值與完成收盤路徑檢討", "", "2026-10-28。固定三個候選，僅診斷、不新增策略版本。月收益來自小時快照淨值，包含浮動持倉；交易退出月的結算PnL另列，兩者不可混用。", "",
        "路徑只用進場起至退出前的小時完成收盤，排除退出當根，避免把退出後價格當可獲取路徑。R=初始成交價至初始止損的價格距離，不含費用；有過+1R收盤後仍淨虧是事後檢討，不代表當時能在+1R無滑價平倉。", "",
        "|候選|年|成本倍數|盈利月份|最差月收益|已到+1R收盤後淨虧筆數|總筆數|", "|---|---:|---:|---:|---:|---:|---:|"]
    for name in files:
        rows=json.loads((root/name).read_text())['rows']
        if len(rows)!=4 or {(r['year'],r['cost_multiplier']) for r in rows}!={(2024,1),(2024,2),(2025,1),(2025,2)}:
            raise ValueError("all unique cases required")
        for row in rows:
            if row['status']!='completed':
                raise ValueError("failed evidence needs explicit review")
            result=row['result'];months=monthly_equity(result,row['year'])
            paths=[];groups=defaultdict(lambda:dict(count=0,losses=0,lost_after_1r_close=0,pnl=0.))
            for trade in result['trades']:
                start=bisect_left(times,trade['entry_timestamp_ms'])
                end=bisect_left(times,trade['exit_timestamp_ms'])
                path=completed_close_path(trade,tape[start:end])
                paths.append(dict(position_id=trade['position_id'],sleeve=trade['sleeve'],direction=trade['direction'],pnl=trade['pnl'],**path))
                g=groups[f"{trade['sleeve']}/{trade['direction']}"]
                g['count']+=1;g['losses']+=trade['pnl']<0;g['lost_after_1r_close']+=path['lost_after_1r_close'];g['pnl']+=trade['pnl']
            positive=sum(m['return_fraction']>0 for m in months)
            worst=min(months,key=lambda m:m['return_fraction'])
            givebacks=sum(p['lost_after_1r_close'] for p in paths)
            cases.append(dict(variant=row['variant'],year=row['year'],cost=row['cost_multiplier'],
                months=months,paths=paths,groups=dict(groups)))
            summary.append(f"|{row['variant']}|{row['year']}|{row['cost_multiplier']}|{positive}/12|{worst['month']} {worst['return_fraction']:+.3%}|{givebacks}|{len(paths)}|")
            if row['cost_multiplier']==1:
                print(row['variant'],row['year'],'positive months',positive,'givebacks',givebacks,'groups',dict(groups))
    sources={name:sha256((root/name).read_bytes()).hexdigest() for name in files}
    sources[str(tape_path)]=sha256(tape_path.read_bytes()).hexdigest()
    (root/"monthly-path-diagnostics.json").write_text(json.dumps(dict(sources=sources,cases=cases,
        used_for_tuning=True,independent_validation=False,not_entry_features=True),indent=2),encoding="utf-8")
    summary += ["", "## 本次關鍵發現", "", "原掃單＋波段效率候選在2025一般成本，短線多單虧損11筆、短線空單19筆；這30筆沒有任何一筆在退出前完成小時收盤到過+1R。波段29筆虧損中則有6筆曾到+1R。因此短線不能主要歸因『已賺到卻沒保住』，盈利保護只能是波段待研究方向，不能保證修好短線進場。收盤路徑不涵蓋盤中wick，不能推論盤中從未到過+1R。", "",
        "一般成本2025盈利月份：原候選4/12、回撤5/12、回撤重置4/12；2024分別6/12、4/12、4/12。增加盈利月份也不等於全年盈利，必須看月度盈虧幅度及年度淨值；不能把回撤模型5個盈利月挑出來宣稱更穩定。", "",
        "## 研究決策", "", "本輪不新增策略候選：先將已失敗假說與可疑方向正式記錄，避免把事後+1R路徑直接變成獲利宣稱。後續若測盈利保護，需先說明它可能犧牲哪些已盈利交易，再於下一根可成交價、原費率、完整跨年與雙成本下單項測試。沒有計算此規則的候選收益，也未將它升格為建議。", "",
        "2024／2025已反覆用於開發，所有月份也都是調參資料，不可選盈利月稱驗證。預先登記真正未看過的期間後才能談獨立驗證；本輪沒有宣稱已完成該驗證。年目標仍每年淨10%、回撤≤10%，尚無達標方案。不掃參數，不降低成本或加槓桿，不改live/paper/testnet。完整四成本／年度案例及逐筆路徑保存data/monthly-path-diagnostics.json。"]
    Path("docs/research/2026-10-28-monthly-path-review.md").write_text("\n".join(summary)+"\n",encoding="utf-8")
    (root/"research-decision-2026-10-28.json").write_text(json.dumps(dict(status="completed_no_change",
        reason="Experience integrated; monthly/path diagnostics are tuning evidence, not yet an executable profit-protection comparison.",
        experience_sha256=sha256((root/"research-experience.json").read_bytes()).hexdigest(),
        diagnostics_sha256=sha256((root/"monthly-path-diagnostics.json").read_bytes()).hexdigest(),
        new_strategy_version=None,orders_submitted=False),indent=2),encoding="utf-8")
    print(f"Saved {len(experience['lessons'])} lessons, {len(cases)} diagnostic cases; no new strategy version.")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--ledger-only",action="store_true")
    main(ledger_only=parser.parse_args().ledger_only)
