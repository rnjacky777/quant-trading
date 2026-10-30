"""Development trial 2: BTC quarterly basis carry, walk-forward over thresholds (choose 2022-23, check 2024-25)."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.basis_carry import Contract, run_basis_carry
from app.backtest.funding_carry import CarryConfig
from app.data.models import Candle, MarkPriceCandle
from scripts.fetch_btc_quarterly import CONTRACTS, ROOT, delivery_ms
from scripts.fetch_btc_spot_2022_2023 import KNOWN_OUTAGES
from scripts.research_funding_carry import COSTS, spot_candles

OUTPUT = Path("data/basis-carry-research.json")
DESIGN = Path("docs/research/2026-10-30-basis-carry-design.md")
THRESHOLDS = (0.0, .03, .06)
SOURCES = ("app/backtest/basis_carry.py", "app/backtest/funding_carry.py", "scripts/research_basis_carry.py", str(DESIGN))
PERP_CARRY = Path("data/funding-carry-research.json")


def contracts() -> list[Contract]:
    out = []
    for code in CONTRACTS:
        rows = json.loads((ROOT / code / "klines.json").read_text(encoding="utf-8"))
        marks = json.loads((ROOT / code / "markPriceKlines.json").read_text(encoding="utf-8"))
        out.append(Contract(code, delivery_ms(code),
                            {r["open_time"]: Candle("binance-usdm", "BTC/USDT", "1h", r["open_time"], r["open"], r["high"],
                                                    r["low"], r["close"], r["volume"]) for r in rows},
                            {r["open_time"]: MarkPriceCandle("binance-usdm", "BTC/USDT", r["open_time"], r["open"], r["high"],
                                                             r["low"], r["close"], timeframe="1h") for r in marks}))
    return out


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    spot, book = spot_candles(), contracts()
    rows = []
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        for case, costs in COSTS.items():
            for threshold in THRESHOLDS:
                result = run_basis_carry(spot, book, CarryConfig(*costs), threshold, start, end, frozenset(KNOWN_OUTAGES))
                rows.append(dict(year=year, cost_case=case, threshold=threshold, result=result))
                m = result["metrics"]
                print(year, case, threshold, f"return={m['total_return']:+.3%} dd={m['maximum_drawdown']:.2%}",
                      f"invested={result['invested_hours']} fees={result['fees']:.1f}", flush=True)
    perp = {(r["year"], r["cost_case"]): r["result"]["metrics"]["total_return"]
            for r in json.loads(PERP_CARRY.read_text(encoding="utf-8"))["rows"]}

    def ret(year: int, case: str, threshold: float) -> float:
        return next(r["result"]["metrics"]["total_return"] for r in rows
                    if (r["year"], r["cost_case"], r["threshold"]) == (year, case, threshold))
    selection = {th: (ret(2022, "primary", th) + ret(2023, "primary", th)) / 2 for th in THRESHOLDS}
    chosen = max(THRESHOLDS, key=lambda th: (round(selection[th], 12), th))
    chosen_rows = [r for r in rows if r["threshold"] == chosen]
    worst = min(r["result"]["metrics"]["total_return"] for r in chosen_rows)
    perp_worst = min(perp.values())
    check = (ret(2024, "primary", chosen) + ret(2025, "primary", chosen)) / 2
    perp_check = (perp[(2024, "primary")] + perp[(2025, "primary")]) / 2
    drawdown = min(r["result"]["metrics"]["maximum_drawdown"] for r in chosen_rows)
    liquidations = sum(r["result"]["liquidated_at_ms"] is not None for r in chosen_rows)
    checks = dict(selection_mean_2022_2023=selection, chosen_threshold=chosen, worst_year=worst, perp_worst_year=perp_worst,
                  check_2024_2025=check, perp_check_2024_2025=perp_check, worst_drawdown=drawdown, liquidations=liquidations,
                  passed=worst > perp_worst and check >= perp_check - .01 and liquidations == 0 and drawdown >= -.10)
    artifact = dict(schema="basis_carry_walkforward_v1", design=str(DESIGN), development_trial=2,
                    trials_in_this_experiment=len(THRESHOLDS), sealed_data_used=False,
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
                    data_manifest_sha256=sha256((ROOT / "manifest.json").read_bytes()).hexdigest(),
                    rows=rows, checks=checks,
                    decision="eligible_for_sealed_validation_request" if checks["passed"] else "reject")
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(dict(checks=checks, decision=artifact["decision"]), indent=1))


if __name__ == "__main__":
    main()
