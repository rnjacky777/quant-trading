"""Development trial 3: multi-coin funding carry, walk-forward over K (choose 2022-23, check 2024-25)."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.funding_carry import CarryConfig
from app.backtest.multi_carry import CoinTape, run_multi_carry
from scripts.fetch_btc_spot_2022_2023 import KNOWN_OUTAGES
from scripts.fetch_multi_coin_carry import ROOT
from scripts.research_funding_carry import COSTS

OUTPUT = Path("data/multi-coin-carry-research.json")
DESIGN = Path("docs/research/2026-10-30-multi-coin-carry-design.md")
KS = (3, 5, 10)
SOURCES = ("app/backtest/multi_carry.py", "app/backtest/funding_carry.py", "scripts/research_multi_coin_carry.py",
           "scripts/fetch_multi_coin_carry.py", str(DESIGN))
BTC_CARRY = Path("data/funding-carry-research.json")


def tapes(meta: dict) -> dict[str, CoinTape]:
    out = {}
    for path in sorted((ROOT / "hourly").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        factor = meta["pairs"][path.stem][1]
        series = {k: {int(t): tuple(v) for t, v in data.get(k, [])} for k in ("perp", "marks", "spot")}
        spot = {t: tuple(p * factor for p in v) for t, v in series["spot"].items()}
        out[path.stem] = CoinTape(path.stem, series["perp"], series["marks"], spot,
                                  sorted((int(t), r) for t, r in data.get("funding", [])))
    return out


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    meta = json.loads((ROOT / "universe.json").read_text(encoding="utf-8"))
    coins = tapes(meta)
    rows = []
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        for case, costs in COSTS.items():
            for k in KS:
                result = run_multi_carry(coins, meta["universe"], CarryConfig(*costs), k, start, end, frozenset(KNOWN_OUTAGES))
                rows.append(dict(year=year, cost_case=case, k=k, result=result))
                m = result["metrics"]
                print(year, case, k, f"return={m['total_return']:+.3%} dd={m['maximum_drawdown']:.2%}",
                      f"funding={result['funding_income']:.0f} fees={result['fees']:.0f}",
                      f"liq={len(result['liquidations'])} exits={len(result['data_exits'])}", flush=True)
    btc = {(r["year"], r["cost_case"]): r["result"]["metrics"]["total_return"]
           for r in json.loads(BTC_CARRY.read_text(encoding="utf-8"))["rows"]}

    def ret(year: int, case: str, k: int) -> float:
        return next(r["result"]["metrics"]["total_return"] for r in rows if (r["year"], r["cost_case"], r["k"]) == (year, case, k))
    selection = {k: (ret(2022, "primary", k) + ret(2023, "primary", k)) / 2 for k in KS}
    chosen = max(KS, key=lambda k: (round(selection[k], 12), k))
    chosen_rows = [r for r in rows if r["k"] == chosen]
    check = (ret(2024, "primary", chosen) + ret(2025, "primary", chosen)) / 2
    btc_check = (btc[(2024, "primary")] + btc[(2025, "primary")]) / 2
    worst = min(r["result"]["metrics"]["total_return"] for r in chosen_rows)
    drawdown = min(r["result"]["metrics"]["maximum_drawdown"] for r in chosen_rows)
    liquidations = sum(len(r["result"]["liquidations"]) for r in chosen_rows)
    checks = dict(selection_mean_2022_2023=selection, chosen_k=chosen, check_2024_2025=check, btc_check_2024_2025=btc_check,
                  worst_year=worst, btc_worst_year=min(btc.values()), worst_drawdown=drawdown, liquidations=liquidations,
                  year_2022_primary=ret(2022, "primary", chosen), btc_2022_primary=btc[(2022, "primary")])
    checks["passed"] = (check >= btc_check + .005 and worst >= checks["btc_worst_year"] and liquidations == 0
                        and drawdown >= -.10 and checks["year_2022_primary"] > checks["btc_2022_primary"])
    artifact = dict(schema="multi_coin_carry_walkforward_v1", design=str(DESIGN), development_trial=3,
                    trials_in_this_experiment=len(KS), sealed_data_used=False,
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
                    universe_sha256=sha256((ROOT / "universe.json").read_bytes()).hexdigest(),
                    rows=rows, checks=checks,
                    decision="eligible_for_forward_paper_registration" if checks["passed"] else "reject")
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(dict(checks=checks, decision=artifact["decision"]), indent=1))


if __name__ == "__main__":
    main()
