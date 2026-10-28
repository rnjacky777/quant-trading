"""Audit the pullback replacement and retain the failed experiment."""
from bisect import bisect_left
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.backtest.frequency import entry_frequency
from app.data.models import Candle
from app.strategies.directional_pullback import DirectionalPullbackStrategy


def main() -> None:
    parent_path=Path("data/perpetual-confirmed-efficiency.json")
    child_path=Path("data/perpetual-directional-pullback.json")
    tape_path=Path("data/btc-perpetual-1h/klines.json")
    parents={(r['year'],r['cost_multiplier']):r for r in json.loads(parent_path.read_text())['rows']}
    rows=json.loads(child_path.read_text())['rows']
    assert len(rows)==4 and {(r['year'],r['cost_multiplier']) for r in rows}==set(parents)
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads(tape_path.read_text())]
    times=[c.timestamp_ms for c in tape]
    cases=[];details=[]
    lines=["# 對稱趨勢回撤恢復：完整結果與失敗證據", "",
        "2026-10-28。portfolio_confirmed_efficiency → portfolio_directional_pullback，單項替換短線signal，波段／出場／風險／成本不變；全部父指紋及完整快照逐一重播一致。每年重設10,000USDT，一般單邊10bps費＋5bps滑價，雙成本20bps＋10bps，含實際funding。", "",
        "## 結論", "", "未採用。兩年一般及雙成本收益全部比父候選差，2024雙成本回撤超過10%。增加交易不代表增加有效優勢；保留原父候選研究參考，而非宣稱原候選已通過盈利目標。", "",
        "## 全部四筆結果", "", "|年|成本倍數|父收益|新收益|新回撤|父短線筆數|新短線筆數|新總筆數|短線日均|", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        parent=parents[(row['year'],row['cost_multiplier'])]
        assert row['status']==parent['status']=='completed'
        for key in ('input_fingerprints','config','portfolio_limits'):
            assert row[key]==parent[key]
        for new,old in zip(row['sleeves'],parent['sleeves'],strict=True):
            assert new['name']==old['name'] and new['config']==old['config']
            if new['name']=='swing':
                assert new==old
        r=row['result'];trades=r['trades'];m=r['metrics'];pm=parent['result']['metrics']
        f=entry_frequency(trades,row['year']);pf=entry_frequency(parent['result']['trades'],row['year'])
        assert isclose(r['final_equity'],10000+sum(t['pnl'] for t in trades),abs_tol=1e-7)
        assert len({t['position_id'] for t in trades})==len(trades)
        assert all(t['leverage']==1 for t in trades)
        assert max(Counter(t['entry_timestamp_ms']//86400000 for t in trades).values())<=2
        accepted=[a for a in r['admissions'] if a['status']=='accepted']
        assert {a['position_id'] for a in accepted}=={t['position_id'] for t in trades}
        for a in accepted:
            eq=a['equity_before'];limits=row['portfolio_limits']
            assert a['gross_before']+max(a['gross_added'],a['entry_notional'])<=eq*limits['max_gross_exposure']+1e-7
            assert a['stop_risk_before']+a['planned_risk']<=eq*limits['max_open_stop_risk']+1e-7
            assert a['margin_before']+a['margin_added']+a['entry_fee']<=min(a['cash_before'],eq*limits['max_margin_fraction'])+1e-7
        grouped=defaultdict(lambda:dict(count=0,pnl=0.));checked=0
        for t in trades:
            g=grouped[f"{t['sleeve']}/{t['direction']}/{t['exit_reason']}"]
            g['count']+=1;g['pnl']+=t['pnl']
            if t['sleeve']=='intraday':
                index=bisect_left(times,t['entry_timestamp_ms'])
                signal=DirectionalPullbackStrategy().generate(tape[:index])
                assert signal.direction==t['direction']
                assert isclose(signal.stop_loss_price,t['stop_loss_price'],abs_tol=1e-8)
                assert signal.timestamp.timestamp()*1000==times[index]-3600000
                checked+=1
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{pm['total_return']:+.3%}|{m['total_return']:+.3%}|{m['maximum_drawdown']:.3%}|{pf['intraday']}|{f['intraday']}|{f['total']}|{f['intraday_daily_average']:.3f}|")
        evidence=dict(year=row['year'],cost=row['cost_multiplier'],metrics=m,frequency=f,
            parent_frequency=pf,grouped=dict(grouped),intraday_entries_recomputed=checked,checks="passed")
        cases.append(evidence)
        details += ["",f"## {row['year']}／成本{row['cost_multiplier']}倍完整指標及分組","",
            "收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding與頻率：", "",
            "```json",json.dumps(evidence,indent=2),"```"]
    lines += ["", "## 機會與成本診斷", "",
        "原始4h方向／1h回撤恢復事件2024有411次、2025有400次；ATR門檻後254／151次。這是執行前機會，尚未套退出日、風險與每日名額，不當成交。合格ATR/close中位數0.810%／0.757%，只約雙成本來回費／滑價0.6%的1.35／1.26倍，且不含funding；ATR是波動，不能當預期利潤。保存data/pullback-opportunity-diagnostics.json。", "",
        "組合策略共用名額與風險，短線改動也會影響波段交易與資金路徑，不能把收益差全歸因短線本身或費用。詳細策略／方向／退出原因在各成本案例分開保存，不加總重疊樣本。", "",
        "## 外部研究與後續可辯護方向", "",
        "檢閱[Liu與Tsyvinski原研究](https://www.nber.org/papers/w24877)及[論文](https://www.nber.org/system/files/working_papers/w24877/w24877.pdf)：研究報告日／週頻率的加密貨幣時間序列動能，不直接支持1h均線回撤或此處的成本後策略。不能因論文有動能結果，就把本次失敗包裝成已驗證策略；也不把該歷史樣本直接外推2024／2025。", "",
        "下一個待驗證假說應先回到交易級診斷：把回撤恢復後的損失按多空、首次／同方向重複恢復事件、進場時已知成本空間與退出原因拆解，檢查是否是高頻來回交叉重複消耗風險及成本。先保存診斷再決定是否有理由測試事件重置／冷卻，不盲掃SMA長度、ATR門檻或加槓桿。本輪不再新增另一個候選。", "",
        "## 可重現與限制", "",
        "203項pytest通過。所有實際短線進場以進場前完成資料重算方向／時間／止損；核對現金、獨立部位ID、1x、每日≤2，以及每次新增的gross／stoprisk／margin預算。交易成本、失敗期間及完整曲線保留data/perpetual-directional-pullback.json。儀表板名稱多空趨勢回撤恢復（未採用），未覆寫父結果。", "",
        "2024／2025均為調參證據、非未見驗證。固定BTC有市場選樣限制，不能推廣到其他資產。仍有1h盤中路徑、固定MMR2%非歷史級距、下單精度／最小量、深度及實際滑價、虛擬研究部位與交易所倉位映射等限制；進場預算非永久持倉比例上限。未改live/paper/testnet，未下單。"]
    report=Path("docs/research/2026-10-28-pullback-results.md")
    report.write_text("\n".join(lines+details)+"\n",encoding="utf-8")
    paths=[parent_path,child_path,tape_path,Path(__file__),Path("app/strategies/directional_pullback.py"),
        Path("scripts/research_directional_pullback.py"),Path("scripts/research_portfolio_overlap.py"),Path("data/pullback-opportunity-diagnostics.json")]
    Path("data/directional-pullback-audit.json").write_text(json.dumps(dict(status="completed_not_adopted",
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},cases=cases),indent=2),encoding="utf-8")
    print(f"All four cases and actual intraday entries audited: {report}")
    for c in cases:
        print(c['year'],c['cost'],c['frequency']['intraday'],c['frequency']['total'])


if __name__=="__main__":
    main()
