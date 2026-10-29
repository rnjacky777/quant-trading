"""Development trial 1: funding-pause carry with walk-forward (choose N on 2022-23, check 2024-25)."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.funding_carry import CarryConfig, run_funding_carry
from app.data.models import FundingRate
from scripts.fetch_btc_spot_2022_2023 import KNOWN_OUTAGES
from scripts.research_eth_carry import inputs as eth_inputs
from scripts.research_funding_carry import COSTS, spot_candles
from scripts.research_risk_budget import late_inputs
from scripts.validate_baseline_2022_2023 import load_inputs

OUTPUT = Path("data/carry-funding-pause-research.json")
DESIGN = Path("docs/research/2026-10-29-carry-funding-pause-design.md")
WINDOWS = (9, 21, 42)
SOURCES = ("app/backtest/funding_carry.py", "scripts/research_carry_funding_pause.py", str(DESIGN))
PARENTS = {"BTC": Path("data/funding-carry-research.json"), "ETH": Path("data/eth-carry-research.json")}


def assets() -> dict:
    early, late = load_inputs(), late_inputs()
    btc_tape = {c.timestamp_ms: c for c in early[0] + late[0]}
    btc_marks = {m.timestamp_ms: m for m in early[1] + late[1]}
    btc_funding = sorted({f.timestamp_ms: f for f in early[2] + late[2]}.values(), key=lambda f: f.timestamp_ms)
    tape, marks, funding, spot, _ = eth_inputs()
    warm = [FundingRate("binance-usdm", "ETH/USDT", int(f["fundingTime"]), float(f["fundingRate"]), 1.0)
            for f in json.loads(Path("data/eth-perpetual-1h/funding-warmup-2021-12.json").read_text(encoding="utf-8"))]
    return dict(BTC=(btc_tape, btc_marks, btc_funding, spot_candles()),
                ETH=({c.timestamp_ms: c for c in tape}, {m.timestamp_ms: m for m in marks}, warm + funding, spot))


def run(data: tuple, year: int, costs: tuple, window: int) -> dict:
    tape, marks, funding, spot = data
    start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    hours = range(start, end, 3600000)
    result = run_funding_carry([tape[t] for t in hours], [marks[t] for t in hours],
                               [f for f in funding if start <= f.timestamp_ms < end], {t: spot[t] for t in hours if t in spot},
                               CarryConfig(*costs, pause_funding_events=window), frozenset(KNOWN_OUTAGES),
                               funding_history=[f for f in funding if f.timestamp_ms < start])
    result.pop("equity_curve")
    return result


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    data = assets()
    rows = []
    for asset, path in PARENTS.items():
        parents = {(r["year"], r["cost_case"]): r["result"]["metrics"] for r in json.loads(path.read_text(encoding="utf-8"))["rows"]}
        for year in range(2022, 2026):
            for case, costs in COSTS.items():
                parent = run(data[asset], year, costs, 0)
                if parent["metrics"] != parents[(year, case)]:
                    raise ValueError(f"{asset} {year} {case}: parent reproduction failed")
                rows.append(dict(asset=asset, year=year, cost_case=case, window=0, result=parent, reproduction="metrics_equal"))
                for window in WINDOWS:
                    rows.append(dict(asset=asset, year=year, cost_case=case, window=window, result=run(data[asset], year, costs, window)))
        print(asset, "parent reproduced (16 cases)", flush=True)

    def ret(asset: str, year: int, case: str, window: int) -> float:
        return next(r["result"]["metrics"]["total_return"] for r in rows
                    if (r["asset"], r["year"], r["cost_case"], r["window"]) == (asset, year, case, window))

    print("\nprimary-cost returns (pause window N; 0 = parent):")
    for asset in PARENTS:
        for window in (0, *WINDOWS):
            print(f"  {asset} N={window:2d} " + " ".join(f"{y}:{ret(asset, y, 'primary', window):+.2%}" for y in range(2022, 2026)))
    selection = {w: sum(ret(a, y, "primary", w) for a in PARENTS for y in (2022, 2023)) / 4 for w in WINDOWS}
    chosen = max(WINDOWS, key=lambda w: (round(selection[w], 12), w))
    check_child = sum(ret(a, y, "primary", chosen) for a in PARENTS for y in (2024, 2025)) / 4
    check_parent = sum(ret(a, y, "primary", 0) for a in PARENTS for y in (2024, 2025)) / 4
    worst_child = min(ret(a, y, c, chosen) for a in PARENTS for y in range(2022, 2026) for c in COSTS)
    worst_parent = min(ret(a, y, c, 0) for a in PARENTS for y in range(2022, 2026) for c in COSTS)
    liquidations = sum(1 for r in rows if r["window"] == chosen and r["result"]["liquidated_at_ms"] is not None)
    checks = dict(selection_mean_2022_2023=selection, chosen_window=chosen,
                  check_2024_2025_child=check_child, check_2024_2025_parent=check_parent,
                  worst_year_child=worst_child, worst_year_parent=worst_parent, liquidations=liquidations,
                  passed=check_child >= check_parent - .0025 and worst_child > worst_parent and liquidations == 0)
    artifact = dict(schema="carry_funding_pause_walkforward_v1", design=str(DESIGN), development_trial=1,
                    trials_in_this_experiment=len(WINDOWS), sealed_data_used=False,
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
                    rows=rows, checks=checks, decision="eligible_for_sealed_validation_request" if checks["passed"] else "reject")
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(dict(checks=checks, decision=artifact["decision"]), indent=1))
    for asset in PARENTS:
        for year in range(2022, 2026):
            r = next(x["result"] for x in rows if (x["asset"], x["year"], x["cost_case"], x["window"]) == (asset, year, "primary", chosen))
            print(f"  {asset} {year} N={chosen}: pauses={r['pauses']} invested_hours={r['invested_hours']} funding={r['funding_income']:.1f} fees={r['fees']:.1f}")


if __name__ == "__main__":
    main()
