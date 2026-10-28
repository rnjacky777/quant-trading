"""Audit the web-inspired pattern candidate, including skipped original winners."""
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
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.sweep_structural_stop import DirectionalSweepStructuralStopStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy


def main() -> None:
    parent_path=Path("data/perpetual-directional-loss-guard.json")
    child_path=Path("data/perpetual-sweep-structure-confirm.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    payload=json.loads(child_path.read_text());rows=payload['rows']
    assert payload['category']=='signal' and len(rows)==4
    assert {(r['year'],r['cost_multiplier']) for r in rows}==set(parents)
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[];details=[]
    lines=["# 網路策略研究與掃單微結構確認：實際全年驗證", "", "2026-10-28。父portfolio_directional_loss_guard → portfolio_sweep_structure_confirm，只新增一項短線進場微結構門檻；全部結構stop、原退出、波段與方向風控保留。外部來源及事前設計見2026-10-28-web-pattern-design.md。", "",
        "## 搜尋後採取的方向", "", "[LuxAlgo作者Session Sweeps](https://www.tradingview.com/script/KdOv0Dfq-Session-Sweeps-LuxAlgo/)描述掃單後等待結構轉向與其他條件；本輪只借用確認概念，不複製其外匯／5m時段或FVG進場。", "",
        "[LuxAlgo作者Market Structure](https://www.tradingview.com/script/kMDlPZuz-Market-Structure-with-Inducements-Sweeps-LuxAlgo/)區分wick與收盤確認結構；[mickes作者Turtle soup](https://www.tradingview.com/script/AmpHKmaz-Turtle-soup/)使用pivot假突破與轉向確認，不能把後來才確認的pivot畫回去當入場。三根是本次固定工程定義，不是原作者最佳參數，也非完整SMC／CHoCH複現。", "",
        "[Liu與Tsyvinski原研究](https://www.nber.org/papers/w24877)的日／週動能與此1h圖形不同，不引用其收益證明本策略。搜尋到的二手勝率、圖形截圖或人氣未當盈利證據，未取得可信原版age細節就沒有套用。", "",
        "## 圖形如何機械判斷", "", "多單：掃過過去20根低點→收回→下一根完成close超過掃單high，且超過確認之前3根high的最高點→下一根開盤交給風控。空單對稱。三根含掃單及再前2根，不含確認bar；相等或僅wick越過不算。4h方向／原強收盤／ATR入場濾網保留，初始stop仍為當時掃單low／high。", "",
        "## 全部年度及成本", "", "每年10,000USDT，一般單邊費10bps／滑價5bps，雙成本20bps／10bps，另含實際funding，全部1x。父四筆原期間、243h暖機、行情／mark／funding指紋與完整快照（含guard trace）一致後才跑子候選。", "",
        "|年|成本倍數|父淨收益|候選淨收益|父最大回撤|候選最大回撤|總交易數|短線筆數|", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        key=(row['year'],row['cost_multiplier']);parent=parents[key]
        assert row['status']==parent['status']=='completed'
        for field in ('config','portfolio_limits','input_fingerprints','intraday_exit_rule','directional_loss_guard'):
            assert row[field]==parent[field]
        assert row['directional_loss_guard'] is True
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
                (t['exit_reason'] in {'signal','time_limit'} or t['exit_reason']=='stop_loss' and
                 t['direction']*(entry.open-t['stop_loss_price'])<=0)]
            shared=[t['pnl'] for t in known if t['sleeve']==a['sleeve']]
            own=[t['pnl'] for t in known if t['sleeve']==a['sleeve'] and t['direction']==a['direction']]
            assert trace['shared_pnls']==shared and trace['directional_pnls']==own
            multiplier=directional_loss_guard_multiplier(shared,own)
            assert trace['final_brake_multiplier']==trace['sizing_multiplier']==multiplier
            strategy=DirectionalSweepStructureConfirmStrategy() if a['sleeve']=='intraday' else DirectionalSwingEfficiencyStrategy()
            signal=strategy.generate(tape[warmup:i])
            if a['sleeve']=='intraday':
                old=DirectionalSweepStructuralStopStrategy().generate(tape[warmup:i])
                for field in ('action','direction','timestamp','stop_loss_price','exit_long','exit_short'):
                    assert getattr(signal,field)==getattr(old,field)
            _,proposal=LongShortResearchEngine(c)._open(a['equity_before'],entry,signal,multiplier)
            assert proposal is not None
            assert isclose(proposal.quantity*a['scale'],a['quantity'],abs_tol=1e-10)
            assert isclose(proposal.planned_risk*a['scale'],a['planned_risk'],abs_tol=1e-7)
            eq=a['equity_before'];limits=row['portfolio_limits']
            assert a['planned_risk']<=eq*c.risk_per_trade*multiplier+1e-7
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
        excluded=[]
        for t in parent['result']['trades']:
            if t['sleeve']=='intraday':
                i=bisect_left(times,t['entry_timestamp_ms'])
                if DirectionalSweepStructureConfirmStrategy().generate(tape[warmup:i]).direction!=t['direction']:
                    excluded.append(dict(position_id=t['position_id'],pnl=t['pnl'],direction=t['direction'],exit_reason=t['exit_reason']))
        grouped=defaultdict(lambda:dict(count=0,pnl=0.))
        for t in trades:
            g=grouped[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"];g['count']+=1;g['pnl']+=t['pnl']
        f=entry_frequency(trades,row['year'])
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{pm['total_return']:+.3%}|{m['total_return']:+.3%}|{pm['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|{f['intraday']}|")
        evidence=dict(year=row['year'],cost=row['cost_multiplier'],checks="passed",metrics=m,frequency=f,
            grouped=dict(grouped),past_only_risk_trace_checks=len(accepted),excluded_parent_events=excluded,
            excluded_parent_winners=sum(e['pnl']>0 for e in excluded),excluded_parent_pnl=sum(e['pnl'] for e in excluded),
            parent_price_pnl_before_fees_funding=sum(t['pnl']+t['fees']-t['funding'] for t in parent['result']['trades']),
            child_price_pnl_before_fees_funding=sum(t['pnl']+t['fees']-t['funding'] for t in trades),parent_fees=pm['fees'],child_fees=m['fees'])
        cases.append(evidence)
        details += ["",f"## {row['year']}／成本{row['cost_multiplier']}倍完整指標及排除代價", "",
            "收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率及被排除父贏家／輸家：", "",
            "```json",json.dumps(evidence,indent=2),"```"]
    lines += ["", "## 判斷與取捨", "", "四組相較父版本收益與回撤均改善，可保留下一輪研究候選：一般2024+3.570%→+3.920%、2025−2.454%→−1.109%；雙成本2024+0.328%→+2.272%、2025−3.617%→−2.022%。但2025仍虧，年淨10%目標未達；不能稱原作者方案有效或已建立可實盤優勢。", "",
        "頻率代價很大：一般成本短線2024由60→18筆、2025由43→16筆，約日均0.049／0.044，遠低於有機會時每天1–2次的偏好。一般總筆數59／59，雙成本60／59；不把波段數量冒充短線頻率，也不強迫湊單。", "",
        "改善不是全都來自更好的毛價差：2024一般成交價差損益（含滑價、未扣費/funding）由577.76降至517.36USDT，但費用179.19→87.50，成本減少是重要來源；2025價差由−99.18→−23.24、費用141.02→81.13，兩者都有改善，仍未有正價差。只是更少交易並非必然成功，之前三小時確認／回撤模型已失敗。", "",
        "濾網也排除原贏家，逐筆在四筆案例保存；不能將被排除父PnL直接相減當候選收益，因共享名額、數量、連虧guard與波段路徑均可變。沒有加槓桿，沒有降低費率或隱藏雙成本失敗。", "",
        "## 驗證與限制", "", "242項pytest通過：三根只用已完成歷史、相等／wick不通過、多空對稱、原退出及結構stop保留、前綴因果；四筆父完整快照一致，子所有入場、初始stop及risk trace從同243h暖機重算，cash/PnL、ID、每日≤2、1x與gross/stoprisk/margin均核對。", "",
        "2024／2025與15項研究皆調參，不是未見驗證，網路概念選擇也有多重嘗試風險。保留固定BTC選樣、1h盤中路徑、MMR2%非歷史級距、精度／最小量、滑價深度及虛擬部位到交易所映射限制。沒有paper/testnet/live升級或下單。候選data/perpetual-sweep-structure-confirm.json；審計data/structure-confirm-audit.json。"]
    report=Path("docs/research/2026-10-28-web-pattern-results.md")
    report.write_text("\n".join(lines+details)+"\n",encoding="utf-8")
    sources=[parent_path,child_path,tape_path,Path(__file__),Path("app/strategies/sweep_structure_confirm.py"),
        Path("scripts/research_structure_confirm.py"),Path("scripts/research_portfolio_overlap.py"),
        Path("app/backtest/portfolio_research.py"),Path("app/risk/regime.py")]
    Path("data/structure-confirm-audit.json").write_text(json.dumps(dict(status="completed_research_candidate",
        independent_validation=False,sources={str(p):sha256(p.read_bytes()).hexdigest() for p in sources},cases=cases),indent=2),encoding="utf-8")
    print(f"Four cases, structure signals, preserved exits and risk traces audited: {report}")


if __name__=="__main__":
    main()
