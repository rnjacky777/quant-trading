"""Review frozen experiments and recompute each swing entry from prior data."""
from bisect import bisect_left
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

from app.data.models import Candle
from app.strategies.swing_confirmation import DirectionalSwingConfirmationStrategy


def main() -> None:
    parent_path = Path("data/perpetual-pa-smc.json")
    child_path = Path("data/perpetual-pa-smc-confirmation.json")
    tape_path = Path("data/btc-perpetual-1h/klines.json")
    tape = [Candle("binance-usdm", "BTC/USDT", "1h", int(r["open_time"]),
                  *[float(r[k]) for k in ("open", "high", "low", "close", "volume")])
            for r in json.loads(tape_path.read_text())]
    times = [c.timestamp_ms for c in tape]
    parents = {(r["year"], r["cost_multiplier"]): r
               for r in json.loads(parent_path.read_text())["rows"]}
    children = json.loads(child_path.read_text())["rows"]
    assert len(children) == 4
    assert {(r["year"], r["cost_multiplier"]) for r in children} == set(parents)
    audit, detail = [], []
    lines = ["# PA＋SMC：波段延後確認結果", "",
        "2026-10-27。portfolio_pa_smc → portfolio_pa_smc_confirmation，單一signal類別變更：波段突破延後一根完整4H確認，之後下一根1H開盤才成交；不採用較快退出或風險遞減。規則及假說見2026-10-27-pa-smc-confirmation-design.md。",
        "", "每年本金10,000 USDT，BTC多空、多部位共用資金。一般成本為單邊10bps費、5bps滑價；雙成本為20bps／10bps；均含實際funding。全部四筆父快照與資料指紋在研究執行時完整重播一致。",
        "", "|年度|成本倍數|父收益|候選收益|父回撤|候選回撤|交易數|最高同時部位|",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
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
        grouped = defaultdict(lambda: dict(count=0, pnl=0.))
        checked = 0
        for trade in trades:
            key = f"{trade['sleeve']}/{trade['direction']}/{trade['exit_reason']}"
            grouped[key]["count"] += 1
            grouped[key]["pnl"] += trade["pnl"]
            if trade["sleeve"] == "swing":
                index = bisect_left(times, trade["entry_timestamp_ms"])
                assert times[index] == trade["entry_timestamp_ms"]
                signal = DirectionalSwingConfirmationStrategy().generate(tape[:index])
                assert signal.direction == trade["direction"]
                assert signal.timestamp.timestamp() * 1000 == times[index] - 3600000
                assert isclose(signal.stop_loss_price, trade["stop_loss_price"], abs_tol=1e-8)
                checked += 1
        m, p = result["metrics"], parent["result"]["metrics"]
        lines.append(f"|{row['year']}|{row['cost_multiplier']}|{p['total_return']:+.3%}|{m['total_return']:+.3%}|{p['maximum_drawdown']:.3%}|{m['maximum_drawdown']:.3%}|{len(trades)}|{result['maximum_concurrent_positions']}|")
        detail += ["", f"## {row['year']}／成本{row['cost_multiplier']}倍", "",
            "完整指標（含收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding）：",
            "", "```json", json.dumps(m, indent=2), "```", "",
            "部位／方向／退出原因分組（共享名額與資金，不作獨立因果解釋）：", "",
            "```json", json.dumps(dict(grouped), indent=2), "```"]
        audit.append(dict(year=row["year"], cost=row["cost_multiplier"], checks="passed",
            swing_entries_recomputed=checked, grouped=dict(grouped), metrics=m))
    lines += ["", "## 判斷", "",
        "四個期間／成本組合的收益和回撤均優於原PA＋SMC父候選；但2025一般成本仍虧3.935%、雙成本仍虧4.909%，未達兩年各10%目標。2024雙成本只餘0.067%，成本餘裕很薄。可保留作下一輪研究候選，不能升格為可實盤獲利方案，未調高槓桿。",
        "", "強收盤分組沒有跨年一致優勢，已記錄並未實作；下一根延續的事後分組也未拿原進場價當可執行結果。實際候選等確認後才交易，付出較差進場價或錯過行情的代價。事後24h MFE／MAE僅是診斷路徑，可能跨過原退出點，非已實現收益。",
        "", "2024／2025已反覆用於調參，非未見驗證。四筆重疊成本實驗不是四份獨立樣本，不能加總其收益或交易數。193項pytest測試通過。新增測試覆蓋多空、真正前一根突破、下一根完成確認、相等／wick拒絕、保留原止損及退出。逐筆實際波段進場也用截至進場前的完成資料重算方向、時間及止損一致。",
        "", "仍保留1h盤中順序、固定MMR2%非歷史級距、深度與實際滑價、下單精度／最小單量、虛擬多筆隔離與交易所實際倉位模式等限制。未改paper/testnet/live設定、未下單。完整曲線與逐筆交易在data/perpetual-pa-smc-confirmation.json，介面名稱為PA＋SMC波段延後確認（實驗）。",
        "", "下一步先評估剩餘虧損是否集中在特定市場狀態與方向，尤其確認後仍回落的突破；先保存分組結果，再決定是否有足夠依據測試一項條件。不靠提高槓桿把負期望放大，不掃等待根數。"]
    report = Path("docs/research/2026-10-27-pa-smc-confirmation-results.md")
    report.write_text("\n".join(lines + detail) + "\n", encoding="utf-8")
    paths = [parent_path, child_path, tape_path, Path(__file__),
        Path("scripts/analyze_swing_continuation.py"), Path("data/pa-smc-continuation-diagnostics.json"),
        Path("scripts/research_pa_smc_confirmation.py"), Path("scripts/research_portfolio_overlap.py"),
        Path("app/strategies/swing_confirmation.py"), Path("app/strategies/directional_swing.py")]
    Path("data/pa-smc-confirmation-audit.json").write_text(json.dumps(dict(
        sources={str(p): sha256(p.read_bytes()).hexdigest() for p in paths}, cases=audit), indent=2), encoding="utf-8")
    print(f"Audited all four cases and every swing entry; report: {report}")


if __name__ == "__main__":
    main()
