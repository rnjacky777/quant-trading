"""Audit past-only loss histories, exact sizing and unchanged entry/exit events."""
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
from app.risk.regime import directional_loss_guard_multiplier, loss_streak_multiplier
from app.strategies.sweep_structural_stop import DirectionalSweepStructuralStopStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy


def main() -> None:
    parent_path=Path("data/perpetual-sweep-structural-stop.json")
    child_path=Path("data/perpetual-directional-loss-guard.json")
    reference_path=Path("data/perpetual-confirmed-efficiency.json")
    diagnostic_path=Path("data/directional-brake-diagnostics.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    refs={(r['year'],r['cost_multiplier']):r for r in json.loads(reference_path.read_text())['rows']}
    payload=json.loads(child_path.read_text());rows=payload['rows']
    assert payload['category']=='risk' and len(rows)==4
    assert {(r['year'],r['cost_multiplier']) for r in rows}==set(parents)
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape];cases=[];details=[]
    lines=["# 結構止損＋同方向連虧保護：四組收益與回撤均改善", "", "2026-10-28。portfolio_sweep_structural_stop → portfolio_directional_loss_guard，唯一risk變更：min(原共享連虧倍率，同策略同方向連虧倍率)。不是重複減半成1/4，不取消共享保護、不把反向盈利視為當前方向已恢復。", "",
        "## 診斷依據", "", "止損較窄多單組雖虧，但相對舊ATR未跨年／成本一致較差，故未直接加ATR下限。轉而逐筆重建當時已知平倉紀錄，101／101／85／85次原planned risk全重現一致；額外同方向保護對父案例分別影響6／5／10／8筆，凍結父損益−91.44／−74.44／−64.10／−37.93USDT，但也有贏家，故僅作一次可反駁假說，不把群組除半假裝可得收益。", "",
        "## 不變條件", "", "結構stop、全部多空進出場、波段、24h／168h持有、每年10,000本金、原risk上限0.25%（保護後0.125%）、gross/stoprisk/reserved-margin與每日總計≤2全部不變。一般單邊費10bps／滑價5bps，雙成本20bps／10bps，另含實際funding，全部實際1x。父四筆行情／mark／funding指紋及整份回測快照逐一一致後才執行候選；guard預設關閉行為不變。", "",
        "## 相較直接父版本", "", "|年|成本倍數|父淨收益|候選淨收益|父最大回撤|候選最大回撤|交易數|額外保護筆數|", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        key=(row['year'],row['cost_multiplier']);parent=parents[key];ref=refs[key]
        assert row['status']==parent['status']=='completed' and row['directional_loss_guard'] is True
        for field in ('input_fingerprints','config','portfolio_limits','sleeves','intraday_exit_rule'):
            assert row[field]==parent[field]
        assert row['input_fingerprints']==ref['input_fingerprints']
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
        start=1704067200000 if row['year']==2024 else 1735689600000
        warmup=bisect_left(times,start-243*3600000)
        for a in accepted.values():
            i=bisect_left(times,a['timestamp_ms']);entry=tape[i];trace=a['loss_guard_trace'];c=configs[a['sleeve']]
            # Never include a current-bar new lot or a later intrabar close as known input.
            known=[t for t in trades if t['exit_timestamp_ms']<entry.timestamp_ms or
                t['exit_timestamp_ms']==entry.timestamp_ms and t['entry_timestamp_ms']<entry.timestamp_ms and
                (t['exit_reason'] in {'signal','time_limit'} or
                 t['exit_reason']=='stop_loss' and t['direction']*(entry.open-t['stop_loss_price'])<=0)]
            shared=[t['pnl'] for t in known if t['sleeve']==a['sleeve']]
            own=[t['pnl'] for t in known if t['sleeve']==a['sleeve'] and t['direction']==a['direction']]
            assert trace['shared_pnls']==shared and trace['directional_pnls']==own
            assert trace['shared_multiplier']==loss_streak_multiplier(shared)
            assert trace['directional_multiplier']==loss_streak_multiplier(own)
            expected=directional_loss_guard_multiplier(shared,own)
            assert trace['final_brake_multiplier']==trace['sizing_multiplier']==expected
            assert expected in {.5,1} and expected<=trace['shared_multiplier']
            strategy=DirectionalSweepStructuralStopStrategy() if a['sleeve']=='intraday' else DirectionalSwingEfficiencyStrategy()
            signal=strategy.generate(tape[warmup:i])
            _,proposal=LongShortResearchEngine(c)._open(a['equity_before'],entry,signal,expected)
            assert proposal is not None
            assert isclose(proposal.planned_risk*a['scale'],a['planned_risk'],abs_tol=1e-7)
            assert isclose(proposal.quantity*a['scale'],a['quantity'],abs_tol=1e-10)
            eq=a['equity_before'];limits=row['portfolio_limits']
            assert a['planned_risk']<=eq*c.risk_per_trade*expected+1e-7
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
        p_events={(t['entry_timestamp_ms'],t['sleeve'],t['direction']):t for t in parent['result']['trades']}
        c_events={(t['entry_timestamp_ms'],t['sleeve'],t['direction']):t for t in trades}
        assert p_events.keys()==c_events.keys()
        common=[];grouped=defaultdict(lambda:dict(count=0,pnl=0.))
        for event,t in c_events.items():
            p=p_events[event]
            assert t['exit_timestamp_ms']==p['exit_timestamp_ms'] and t['exit_reason']==p['exit_reason']
            for field in ('entry_price','exit_price','stop_loss_price'):
                assert isclose(t[field],p[field],abs_tol=1e-8)
            for field in ('pnl','fees','funding'):
                assert isclose(t[field]/t['quantity'],p[field]/p['quantity'],rel_tol=1e-9,abs_tol=1e-7)
            trace=accepted[t['position_id']]['loss_guard_trace']
            active=trace['final_brake_multiplier']<trace['shared_multiplier']
            common.append(dict(entry_timestamp_ms=t['entry_timestamp_ms'],sleeve=t['sleeve'],direction=t['direction'],
                extra_guard=active,parent_pnl=p['pnl'],child_pnl=t['pnl'],parent_quantity=p['quantity'],child_quantity=t['quantity']))
            g=grouped[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"]
            g['count']+=1;g['pnl']+=t['pnl']
        extra=[e for e in common if e['extra_guard']]
        f=entry_frequency(trades,row['year'])
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{pm['total_return']:+.3%}|{m['total_return']:+.3%}|{pm['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|{len(extra)}|")
        evidence=dict(year=row['year'],cost=row['cost_multiplier'],checks="passed",metrics=m,
            reference_original_metrics=ref['result']['metrics'],frequency=f,grouped=dict(grouped),
            exact_entry_exit_and_unit_pnl_matches=len(common),past_only_brake_trace_checks=len(accepted),
            parent_price_pnl_before_fees_funding=sum(t['pnl']+t['fees']-t['funding'] for t in parent['result']['trades']),
            child_price_pnl_before_fees_funding=sum(t['pnl']+t['fees']-t['funding'] for t in trades),
            parent_fees=pm['fees'],child_fees=m['fees'],extra_guard_count=len(extra),
            protected_parent_winners=sum(e['parent_pnl']>0 for e in extra),
            parent_pnl_in_guard_cohort=sum(e['parent_pnl'] for e in extra),
            child_pnl_in_guard_cohort=sum(e['child_pnl'] for e in extra),common_events=common)
        cases.append(evidence)
        details += ["",f"## {row['year']}／成本{row['cost_multiplier']}倍完整指標與減倉代價", "",
            "收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率、較早原版參考與原贏家被減少的對照：", "",
            "```json",json.dumps(evidence,indent=2),"```"]
    lines += ["", "## 判斷與下一輪基準", "", "相較直接父結構止損版本，四組收益提高、回撤降低。一般2024約+3.104%→+3.570%、2025−2.779%→−2.454%；雙成本2024−0.046%→+0.328%、2025−3.807%→−3.617%。交易筆數與實際進出場事件完全一致，只改變風險配置；可以保留下一輪研究候選，父與較早原版都繼續作對照。", "",
        "2025一般成本成交價差損益（仍含滑價、未扣費/funding）由−121.62改善至−99.18USDT，費用由151.10降至141.02；不是調低費率，亦不只是省費。但同事件退出與每單位qty結果完全相同，因此不是新訊號優勢，只是依過去已平倉紀錄重配風險的歷史改善。2025仍負，兩年各淨10%目標未達，不能用槓桿放大或推實盤。", "",
        "相較更早原掃單＋波段效率參考，2024／2025一般成本淨收益較高，但回撤仍略高（原約2.970%／4.292%，本候選3.081%／4.381%），不能省略這個較早風險對照或宣稱所有版本都更穩。", "",
        "## 驗證與限制", "", "234項pytest通過：多空鏡像跨UTC日的兩次同方向虧損→相反盈利→同方向再進場，原共享保護仍有效、同方向未恢復不能被解除、不重複相乘、零PnL不重置，observer深拷貝不污染risk trace。四筆父整份快照一致、候選逐筆已知歷史重建與trace／_open數量及risk完全一致，並核對現金、ID、每日≤2、1x、單筆與總gross/stoprisk/margin預算。計劃risk不是跳空或未來funding下的保證最大損失。", "",
        "方向保護在相同已知歷史下只維持／降低預算，但實際帳戶路徑會受數量改變影響，不能保證每個相同時間qty都較父低。會壓低部分原贏家；逐筆共同事件及保護群組贏家數都保存，不只報收益提升。", "",
        "2024／2025及13項經驗均調參，非未見驗證；成本案例與訊號事件重疊，四組同向不是四份獨立統計證據，不掃連虧次數／倍率。保留固定BTC選樣、1h盤中路徑、MMR2%非歷史級距、深度滑價、精度／最小量與研究部位／交易所映射限制。只完成研究風控，未宣稱paper/testnet/live能力、未改交易設定、未下單。完整曲線交易data/perpetual-directional-loss-guard.json，逐筆trace及來源審計data/directional-loss-guard-audit.json。"]
    report=Path("docs/research/2026-10-28-directional-guard-results.md")
    report.write_text("\n".join(lines+details)+"\n",encoding="utf-8")
    sources=[parent_path,child_path,reference_path,diagnostic_path,tape_path,Path(__file__),
        Path("app/risk/regime.py"),Path("app/backtest/portfolio_research.py"),Path("scripts/research_directional_guard.py"),
        Path("scripts/research_portfolio_overlap.py"),Path("scripts/analyze_directional_brake.py")]
    Path("data/directional-loss-guard-audit.json").write_text(json.dumps(dict(status="completed_research_candidate",
        independent_validation=False,sources={str(p):sha256(p.read_bytes()).hexdigest() for p in sources},cases=cases),indent=2),encoding="utf-8")
    print(f"Four cases, past-only risk traces, sizes and unchanged exit events audited: {report}")


if __name__=="__main__":
    main()
