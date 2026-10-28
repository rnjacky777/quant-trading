"""Audit every case, entry decision and shared-account admission budget."""
from bisect import bisect_left
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.data.models import Candle
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy


def main() -> None:
    parent_path = Path("data/perpetual-pa-smc-confirmation.json")
    child_path = Path("data/perpetual-confirmed-efficiency.json")
    tape_path = Path("data/btc-perpetual-1h/klines.json")
    diagnostics_path = Path("data/confirmed-failure-diagnostics.json")
    tape = [Candle("binance-usdm", "BTC/USDT", "1h", int(r["open_time"]),
                  *[float(r[k]) for k in ("open", "high", "low", "close", "volume")])
            for r in json.loads(tape_path.read_text())]
    times = [c.timestamp_ms for c in tape]
    parents = {(r["year"], r["cost_multiplier"]): r for r in json.loads(parent_path.read_text())["rows"]}
    children = json.loads(child_path.read_text())["rows"]
    assert len(children) == 4
    assert {(r["year"], r["cost_multiplier"]) for r in children} == set(parents)
    cases, detail = [], []
    lines = ["# 確認後失敗的方向／行情與效率過濾結果", "",
        "2026-10-28。portfolio_pa_smc_confirmation → portfolio_confirmed_efficiency，僅新增波段ER20≥0.3的進場條件。設計在2026-10-28-confirmed-efficiency-design.md預先保存，沒有掃窗口或門檻。",
        "", "## 原父候選虧損集中在哪裡", "",
        "失敗在此指扣費後虧損，不等於證明是假突破。2024一般成本波段多單34筆、19虧，淨+411.56USDT；空單11筆、9虧，淨−96.28。2025多單25筆、17虧，淨−91.70；空單26筆、20虧，淨−171.92。2025空單最差月份為6月4筆−58.56、8月7筆−55.51、3月2筆−48.40；多單1月4筆−64.43與8月3筆−46.48較差。月份僅描述，不作季節交易條件。",
        "", "用進場當時20次4H收盤變動的ER分類：2025低方向效率ER<0.3的波段9筆虧8筆，淨−93.90；ER≥0.3仍有42筆、29虧，淨−169.72。因此不能把全部損失歸因盤整。2024低ER僅6筆，合計約+0.02，樣本很小。2024較高ER空單8筆全虧，淨−107.83，更說明『有趨勢就能做空賺錢』沒有依據。",
        "", "SMA60斜率同向已涵蓋2025全部26筆波段空單，新增同向斜率不能排除它們。2025確認收盤越過原突破wick的多空24筆合計約−267.66，比未越過wick組差，故未再加更強收盤條件。SMA間距≥1ATR的2025多空33筆合計約−271.05，但2024同組盈利，故不依單一年份刪掉它。",
        "", "2025短線多單另虧−114.24、短線空單−15.60，僅改波段無法解決所有來源。分組重疊、部位共享名額及資金，不能把差異解讀為獨立因果，也不能加總重複成本案例。完整四筆方向／月份／行情／退出分組、費用滑價funding與逐筆特徵在data/confirmed-failure-diagnostics.json。",
        "", "## 完整實驗結果", "",
        "每年重設10,000USDT，BTC永續多空、多部位、實際1x。一般單邊費10bps／滑價5bps，雙成本20bps／10bps，含實際funding。四筆父快照與行情／mark／funding指紋完整重播一致才跑子候選。",
        "", "|年|成本倍數|父收益|新收益|父回撤|新回撤|交易數|最高同時部位|",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in children:
        parent = parents[(row["year"], row["cost_multiplier"])]
        assert row["status"] == parent["status"] == "completed"
        for field in ("input_fingerprints", "config", "portfolio_limits"):
            assert row[field] == parent[field]
        for new, old in zip(row["sleeves"], parent["sleeves"], strict=True):
            assert new["name"] == old["name"] and new["config"] == old["config"]
            if new["name"] == "intraday":
                assert new == old
        result = row["result"]
        trades = result["trades"]
        assert len({t["position_id"] for t in trades}) == len(trades)
        assert isclose(result["final_equity"], 10000 + sum(t["pnl"] for t in trades), abs_tol=1e-7)
        assert all(t["leverage"] == 1 for t in trades)
        assert max(Counter(t["entry_timestamp_ms"] // 86400000 for t in trades).values()) <= 2
        accepted = [a for a in result["admissions"] if a["status"] == "accepted"]
        assert {a["position_id"] for a in accepted} == {t["position_id"] for t in trades}
        limits = row["portfolio_limits"]
        for a in accepted:
            eq = a["equity_before"]
            assert a["gross_before"] + max(a["gross_added"], a["entry_notional"]) <= eq * limits["max_gross_exposure"] + 1e-7
            assert a["stop_risk_before"] + a["planned_risk"] <= eq * limits["max_open_stop_risk"] + 1e-7
            assert a["margin_before"] + a["margin_added"] + a["entry_fee"] <= min(a["cash_before"], eq * limits["max_margin_fraction"]) + 1e-7
        grouped = defaultdict(lambda: dict(count=0, pnl=0.))
        checked = 0
        for trade in trades:
            key = f"{trade['sleeve']}/{trade['direction']}/{trade['exit_reason']}"
            grouped[key]["count"] += 1
            grouped[key]["pnl"] += trade["pnl"]
            if trade["sleeve"] == "swing":
                index = bisect_left(times, trade["entry_timestamp_ms"])
                signal = DirectionalSwingEfficiencyStrategy().generate(tape[:index])
                assert signal.direction == trade["direction"]
                assert signal.timestamp.timestamp() * 1000 == times[index] - 3600000
                assert isclose(signal.stop_loss_price, trade["stop_loss_price"], abs_tol=1e-8)
                checked += 1
        m, p = result["metrics"], parent["result"]["metrics"]
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{p['total_return']:+.3%}|{m['total_return']:+.3%}|{p['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|{result['maximum_concurrent_positions']}|")
        detail += ["", f"## {row['year']}／成本{row['cost_multiplier']}倍完整指標", "",
            "包含收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding：", "",
            "```json", json.dumps(m, indent=2), "```", "", "分策略／方向／退出原因（描述性）：", "",
            "```json", json.dumps(dict(grouped), indent=2), "```"]
        cases.append(dict(year=row["year"], cost=row["cost_multiplier"], checks="passed",
            swing_entries_recomputed=checked, admission_budgets_checked=len(accepted), metrics=m, grouped=dict(grouped)))
    lines += ["", "## 判斷、來源與限制", "",
        "一般成本兩年收益及回撤改善；2025雙成本也改善，但2024雙成本由+0.067%降至−0.081%，回撤由3.951%增至4.217%，所以不是全面優勝。2025仍虧3.003%，不達每年淨收益10%目標；僅保留研究候選，不增加槓桿或實盤部署。",
        "", "ER概念參考[QuantConnect官方文件](https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators/kaufman-efficiency-ratio)與[官方LEAN實作](https://github.com/QuantConnect/Lean/blob/master/Indicators/KaufmanEfficiencyRatio.cs)。本次明定20次變動，零路徑回傳0；非完全相同暖機慣例。這些來源沒有證明0.3為最佳值或BTC有正期望，門檻只有本次事前固定測試的意義。",
        "", "196項pytest測試通過；驗證多空對稱、完成4H、過濾不阻擋退出、趨勢時止損一致、效率計算及尺度不變。保存審計核對四筆資料指紋、父設定不變、現金／逐筆損益對帳、部位ID、每日≤2、全部1x、每次進場的總曝險／總止損風險／不可重用保證金上限；逐筆波段訊號用截至進場前資料重算。這些是進場限制，不宣稱持倉後市場變動永不超標。",
        "", "2024／2025均已用於調參，非未見驗證。只研究事前固定BTC，未處理其他市場的倖存者選樣；無跨資產可泛化證據。仍有1h盤中路徑、平面MMR2%非歷史級距、深度／滑價、實際下單精度及最小單量、虛擬獨立部位與交易所實際倉位模式差異。未改paper/testnet/live，未下單。完整曲線及交易在data/perpetual-confirmed-efficiency.json，儀表板名稱PA＋SMC確認後效率過濾（實驗）。"]
    report = Path("docs/research/2026-10-28-confirmed-efficiency-results.md")
    report.write_text("\n".join(lines + detail) + "\n", encoding="utf-8")
    paths = [parent_path, child_path, tape_path, diagnostics_path, Path(__file__),
        Path("scripts/analyze_confirmed_failures.py"), Path("scripts/research_confirmed_efficiency.py"),
        Path("scripts/research_portfolio_overlap.py"), Path("app/strategies/swing_efficiency.py")]
    Path("data/confirmed-efficiency-audit.json").write_text(json.dumps(dict(
        sources={str(p): sha256(p.read_bytes()).hexdigest() for p in paths}, cases=cases), indent=2), encoding="utf-8")
    print(f"All four cases, swing entries and shared budgets audited; report: {report}")


if __name__ == "__main__":
    main()
