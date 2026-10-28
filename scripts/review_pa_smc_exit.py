"""Audit and describe all saved cases; no new parameter search."""
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path


def main() -> None:
    parent_path = Path("data/perpetual-pa-smc.json")
    child_path = Path("data/perpetual-pa-smc-exit.json")
    parents = {(r["year"], r["cost_multiplier"]): r
               for r in json.loads(parent_path.read_text())["rows"]}
    children = json.loads(child_path.read_text())["rows"]
    assert len(children) == 4
    assert {(r["year"], r["cost_multiplier"]) for r in children} == set(parents)
    audit = []
    lines = ["# PA＋SMC：波段較快退出結果", "",
        "2026-10-27。父候選 portfolio_pa_smc → portfolio_pa_smc_fast_exit。只將波段反向通道退出10根4H改為5根；其餘設定不變。設計見2026-10-27-pa-smc-exit-design.md。",
        "", "四筆父候選已在執行腳本中逐一完整快照重播一致，核對行情、mark、funding指紋後才執行候選。每年重設10,000 USDT；含費用、滑價與實際funding；全部實際成交1x。",
        "", "|年度|成本倍數|父收益|新收益|父最大回撤|新最大回撤|交易數|",
        "|---|---:|---:|---:|---:|---:|---:|"]
    detail = []
    for row in children:
        parent = parents[(row["year"], row["cost_multiplier"])]
        assert row["status"] == parent["status"] == "completed"
        assert row["input_fingerprints"] == parent["input_fingerprints"]
        assert row["config"] == parent["config"]
        assert row["portfolio_limits"] == parent["portfolio_limits"]
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
        grouped = defaultdict(lambda: {"count": 0, "pnl": 0.0})
        for trade in trades:
            key = f"{trade['sleeve']}/{trade['direction']}/{trade['exit_reason']}"
            grouped[key]["count"] += 1
            grouped[key]["pnl"] += trade["pnl"]
        m, p = result["metrics"], parent["result"]["metrics"]
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{p['total_return']:+.3%}|{m['total_return']:+.3%}|{p['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|")
        detail += ["", f"## {row['year']}／成本{row['cost_multiplier']}倍", "",
            "全部指標（收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價與funding）：",
            "", "```json", json.dumps(m, ensure_ascii=False, indent=2), "```", "",
            "依部位／方向／退出原因拆解（描述性，非獨立因果貢獻）：", "", "```json",
            json.dumps(dict(grouped), ensure_ascii=False, indent=2), "```"]
        audit.append(dict(year=row["year"], cost=row["cost_multiplier"], checks="passed",
                          grouped=dict(grouped), metrics=m))
    lines += ["", "## 判斷與限制", "",
        "2025虧損與回撤下降，但2024收益由2.123%降至0.135%，且雙成本兩年皆虧損；不取代父候選，不增加槓桿。兩年各淨收益10%目標未通過。較快退出存在截斷贏家的代價，不能用2025改善推論全面較優。",
        "", "下一個研究方向應先量測失敗突破進場後的持續性／最大有利與不利變動，再形成一個可於當時觀察的進場假說；不在5根附近反覆掃參數，也不把事後最大漲跌視為當時可知。",
        "", "2024、2025已用於調參，非未見驗證。未新增資料或提出未經來源支持的市場規律；本輪是對內部交易證據的單項退出實驗。仍有固定MMR2%非歷史級距、1h盤中路徑、虛擬獨立部位與真實交易所倉位差異、精度／最小下單未驗證等原有限制。未改paper/testnet/live或下單。",
        "", "188項pytest測試通過；包含多空對稱的較快通道退出與未完成4H禁止提前退出。所有指標與逐筆資產曲線保存於data/perpetual-pa-smc-exit.json，儀表板候選名稱為PA＋SMC波段快速退出（實驗）。"]
    report = Path("docs/research/2026-10-27-pa-smc-exit-results.md")
    report.write_text("\n".join(lines + detail) + "\n", encoding="utf-8")
    paths = [parent_path, child_path, Path(__file__), Path("scripts/research_pa_smc_exit.py"),
             Path("scripts/research_portfolio_overlap.py"), Path("app/strategies/directional_swing.py")]
    Path("data/pa-smc-exit-audit.json").write_text(json.dumps(dict(
        sources={str(p): sha256(p.read_bytes()).hexdigest() for p in paths}, cases=audit),
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Audited all four cases; report: {report}")


if __name__ == "__main__":
    main()
