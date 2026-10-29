"""One-shot preregistered validation of the frozen research baseline on 2022/2023.

Follows data/validation-preregistration.json: the candidate identity and code
hashes are recorded before the run, each candidate is evaluated once, and all
cases are saved whatever the outcome. Funding events lacking a mark price use the
same-hour mark kline open (disclosed in the output).
"""
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from scripts.research_perpetual_directions import fingerprint

HOUR = 3600000
CANDIDATE = "portfolio_swing_failure_exit"
REGISTRY = Path("data/validation-preregistration.json")
BASELINE = Path("data/perpetual-swing-failure-exit.json")
OUTPUT = Path("data/validation-2022-2023-baseline.json")
PERIODS = {2022: (1640995200000, 1672531200000), 2023: (1672531200000, 1704067200000)}
COSTS = ((5, 5), (10, 5), (20, 10))  # fee_bps, slippage_bps; 10/5 is the preregistered normal case
SOURCES = ("app/backtest/portfolio_research.py", "app/backtest/long_short_research.py", "app/portfolio/research_risk.py",
           "app/risk/regime.py", "app/strategies/sweep_structure_confirm.py", "app/strategies/sweep_structural_stop.py",
           "app/strategies/pa_smc.py", "app/strategies/swing_efficiency.py", "app/strategies/swing_confirmation.py",
           "app/strategies/directional_swing.py", "app/strategies/swing_failure.py", "scripts/validate_baseline_2022_2023.py")


def load_inputs() -> tuple[list[Candle], list[MarkPriceCandle], list[FundingRate], int]:
    early, late = Path("data/btc-perpetual-validation-1h"), Path("data/btc-perpetual-1h")
    split = 1701388800000
    def rows(name: str) -> list[dict]:
        return ([r for r in json.loads((early / name).read_text()) if int(r["open_time"]) < split]
                + [r for r in json.loads((late / name).read_text()) if split <= int(r["open_time"]) < PERIODS[2023][1]])
    tape = [Candle("binance-usdm", "BTC/USDT", "1h", int(r["open_time"]), *[float(r[k]) for k in ("open", "high", "low", "close", "volume")])
            for r in rows("klines.json")]
    marks = [MarkPriceCandle("binance-usdm", "BTC/USDT", int(r["open_time"]), *[float(r[k]) for k in ("open", "high", "low", "close")], timeframe="1h")
             for r in rows("markPriceKlines.json")]
    if [c.timestamp_ms for c in tape] != list(range(tape[0].timestamp_ms, PERIODS[2023][1], HOUR)) or \
            [m.timestamp_ms for m in marks] != [c.timestamp_ms for c in tape]:
        raise ValueError("validation tape is not one continuous hourly series")
    mark_open = {m.timestamp_ms: m.open for m in marks}
    events = ([f for f in json.loads((early / "funding-api.json").read_text()) if int(f["fundingTime"]) < split]
              + [f for f in json.loads((late / "funding-api.json").read_text()) if split <= int(f["fundingTime"]) < PERIODS[2023][1]])
    filled = 0
    funding = []
    for f in events:
        price = float(f["markPrice"]) if f.get("markPrice") else 0.
        if price <= 0:
            price, filled = mark_open[int(f["fundingTime"]) // HOUR * HOUR], filled + 1
        funding.append(FundingRate("binance-usdm", "BTC/USDT", int(f["fundingTime"]), float(f["fundingRate"]), price))
    return tape, marks, funding, filled


def register(registry: dict, parent: dict) -> dict:
    previous = [e for e in registry["evaluations"] if e["candidate"] == CANDIDATE]
    if any(e["status"] == "completed" for e in previous):
        raise ValueError(f"{CANDIDATE} was already evaluated once; preregistration forbids a rerun")
    # A crashed attempt stays on record; the retry is counted, never hidden.
    for e in previous:
        e["status"] = "crashed_attempt"
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", *SOURCES], capture_output=True, text=True).stdout.strip())
    entry = dict(candidate=CANDIDATE, frozen_from=str(BASELINE), status="started", git_head=head, sources_dirty=dirty,
                 source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
                 sleeves=parent["sleeves"], portfolio_limits=parent["portfolio_limits"],
                 engine_flags=dict(directional_loss_guard=True, swing_failure_exit=True),
                 cost_cases=[dict(fee_bps=f, slippage_bps=s) for f, s in COSTS],
                 note="5 bps taker case added after preregistration (verified 2026-10-29), before this evaluation.")
    registry["evaluations"].append(entry)
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


def attribution(trades: list[dict]) -> dict:
    groups: dict[str, dict] = {}
    for t in trades:
        key = f"{t['sleeve']}/{'long' if t['direction'] == 1 else 'short'}"
        g = groups.setdefault(key, dict(trades=0, net_pnl=0., price_pnl=0., wins=0))
        g["trades"] += 1
        g["net_pnl"] += t["pnl"]
        g["price_pnl"] += t["pnl"] + t["fees"] - t["funding"]  # still includes executed slippage
        g["wins"] += t["pnl"] > 0
    return groups


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    parent = next(r for r in json.loads(BASELINE.read_text(encoding="utf-8"))["rows"] if r["cost_multiplier"] == 1)
    tape, marks, funding, filled = load_inputs()
    entry = register(registry, parent)
    strategies = dict(intraday=DirectionalSweepStructureConfirmStrategy(), swing=DirectionalSwingEfficiencyStrategy())
    if any(s["strategy"] != strategies[s["name"]].name for s in parent["sleeves"]):
        raise ValueError("strategy identity differs from frozen baseline")
    rows = []
    for year, (start, end) in PERIODS.items():
        period = [c for c in tape if start - 243 * HOUR <= c.timestamp_ms < end]
        period_marks = [m for m in marks if start <= m.timestamp_ms < end]
        rates = [f for f in funding if start <= f.timestamp_ms < end]
        prints = dict(candles=fingerprint([asdict(c) for c in period]), marks=fingerprint([asdict(m) for m in period_marks]),
                      funding=fingerprint([asdict(f) for f in rates]))
        for fee, slippage in COSTS:
            sleeves = [ResearchSleeve(s["name"], strategies[s["name"]],
                                      replace(PerpetualResearchConfig(**s["config"]), fee_bps=fee, slippage_bps=slippage))
                       for s in parent["sleeves"]]
            result = json.loads(serialize_result(PortfolioResearchEngine(
                sleeves, PortfolioLimits(**parent["portfolio_limits"]), directional_loss_guard=True, swing_failure_exit=True,
            ).run(period, evaluation_start_ms=start, marks=period_marks, funding=rates)))
            groups = attribution(result["trades"])
            m = result["metrics"]
            rows.append(dict(year=year, fee_bps=fee, slippage_bps=slippage, input_fingerprints=prints,
                             metrics=m, attribution=groups, price_pnl=sum(g["price_pnl"] for g in groups.values()), result=result))
            print(year, f"{fee}/{slippage}bps", f"ret={m['total_return']*100:+.2f}% dd={m['maximum_drawdown']*100:.2f}%",
                  f"trades={m['number_of_trades']} sharpe={m['sharpe_ratio']:.2f} pf={m['profit_factor']:.2f}",
                  f"price_pnl={rows[-1]['price_pnl']:+.1f}",
                  {k: (g["trades"], round(g["net_pnl"], 1)) for k, g in sorted(groups.items())})
    normal = [r for r in rows if (r["fee_bps"], r["slippage_bps"]) == (10, 5)]
    passed = all(r["metrics"]["total_return"] > 0 and r["price_pnl"] > 0 for r in normal)
    stress = [r for r in rows if r["fee_bps"] == 20]
    entry.update(status="completed", passed=passed,
                 cost_sensitive=passed and any(r["metrics"]["total_return"] <= 0 for r in stress),
                 funding_mark_price_filled_from_mark_open=filled, output=str(OUTPUT))
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT.write_text(json.dumps(dict(schema="preregistered_validation_v1", candidate=CANDIDATE, rows=rows,
        independent_validation=True, used_for_tuning=False, passed=passed,
        funding_mark_price_filled_from_mark_open=filled), allow_nan=False), encoding="utf-8")
    print("PASSED" if passed else "FAILED", "| funding mark prices filled:", filled)


if __name__ == "__main__":
    main()
