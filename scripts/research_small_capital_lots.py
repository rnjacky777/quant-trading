"""Execution feasibility: frozen trend baseline and BTC carry at 3,000 USDT with Binance lot rounding.

Rounding is applied by wrapping engine internals here; frozen paper sources are not edited.
"""
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path

from app.backtest import funding_carry, portfolio_research
from app.backtest.funding_carry import CarryConfig, run_funding_carry
from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from scripts.fetch_btc_spot_2022_2023 import KNOWN_OUTAGES
from scripts.research_carry_funding_pause import assets
from scripts.research_funding_carry import COSTS as CARRY_COSTS
from scripts.research_risk_budget import COSTS as TREND_COSTS, late_inputs
from scripts.validate_baseline_2022_2023 import load_inputs

OUTPUT = Path("data/small-capital-lots-research.json")
DESIGN = Path("docs/research/2026-10-29-small-capital-lot-design.md")
SOURCES = ("scripts/research_small_capital_lots.py", str(DESIGN))
STEP, PERP_MIN_NOTIONAL = 0.001, 50.0
SETTINGS = ((10000, False), (3000, False), (3000, True))


def floor_step(quantity: float) -> float:
    return math.floor(quantity / STEP + 1e-9) * STEP


def trend_run(engine: PortfolioResearchEngine, rounding: bool, **kwargs) -> tuple[dict, int]:
    """Run with every admitted quantity floored to the exchange step; return result and rejected count."""
    last: dict = {}
    rejected = [0]
    for inner in engine.engines.values():
        original_open = inner._open

        def captured(*args, _open=original_open):
            equity, proposal = _open(*args)
            last["proposal"] = proposal
            return equity, proposal
        inner._open = captured
    original_fraction = portfolio_research.admission_fraction

    def rounded_fraction(**kw):
        fraction, reason = original_fraction(**kw)
        if not rounding or fraction <= 1e-10:
            return fraction, reason
        proposal = last["proposal"]
        quantity = floor_step(proposal.quantity * fraction)
        if quantity < STEP or quantity * proposal.entry_price < PERP_MIN_NOTIONAL:
            rejected[0] += 1
            return 0.0, "below_exchange_minimum"
        return quantity / proposal.quantity, reason
    portfolio_research.admission_fraction = rounded_fraction
    try:
        return json.loads(serialize_result(engine.run(**kwargs))), rejected[0]
    finally:
        portfolio_research.admission_fraction = original_fraction


class LotCarryBook(funding_carry.CarryBook):
    skipped = 0

    def rebalance(self, timestamp_ms: int, spot_open: float, perp_open: float, reason: str) -> None:
        """Parent rebalance with the target floored to the exchange step; small increases are skipped."""
        before = self.equity(spot_open, perp_open)
        target = floor_step(self.config.target_fraction * before / spot_open)
        increase = target - self.short_qty
        if increase > 1e-12 and increase * perp_open < PERP_MIN_NOTIONAL:
            LotCarryBook.skipped += 1
            return
        if target != self.spot_qty:
            self._trade_spot(target - self.spot_qty, spot_open)
        if target != self.short_qty:
            self._trade_short(target - self.short_qty, perp_open)
        after = self.equity(spot_open, perp_open)
        usdt = self.spot_cash + self.perp_wallet
        self.perp_wallet = after - self.spot_qty * spot_open - self.short_qty * (self.short_entry - perp_open)
        self.spot_cash = usdt - self.perp_wallet
        self.rebalances.append(dict(timestamp_ms=timestamp_ms, reason=reason, equity_before=before,
                                    equity_after=after, quantity=target))


def carry_run(data: tuple, year: int, costs: tuple, capital: float, rounding: bool) -> tuple[dict, int]:
    tape, marks, funding, spot = data
    start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    hours = range(start, end, 3600000)
    LotCarryBook.skipped = 0
    funding_carry.CarryBook = LotCarryBook if rounding else portfolio_carry_book
    try:
        result = run_funding_carry([tape[t] for t in hours], [marks[t] for t in hours],
                                   [f for f in funding if start <= f.timestamp_ms < end], {t: spot[t] for t in hours if t in spot},
                                   CarryConfig(*costs, initial_cash=capital), frozenset(KNOWN_OUTAGES))
    finally:
        funding_carry.CarryBook = portfolio_carry_book
    result.pop("equity_curve", None)
    return result, LotCarryBook.skipped


portfolio_carry_book = funding_carry.CarryBook


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("output exists; never overwrite experiment evidence")
    budget = json.loads(Path("data/perpetual-risk-budget-055.json").read_text(encoding="utf-8"))
    limits = PortfolioLimits(**budget["portfolio_limits"])
    saved_trend = {(r["year"], r["fee_bps"], r["slippage_bps"]): r for r in budget["rows"]
                   if r["variant"] == "portfolio_swing_failure_exit"}
    saved_carry = {(r["year"], r["cost_case"]): r["result"]["metrics"] for r in
                   json.loads(Path("data/funding-carry-research.json").read_text(encoding="utf-8"))["rows"]}
    early, late = load_inputs(), late_inputs()
    rows = []
    for year in range(2022, 2026):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        tape, marks, funding = early[:3] if year < 2024 else late
        period = [c for c in tape if start - 243 * 3600000 <= c.timestamp_ms < end]
        for fee, slip in TREND_COSTS:
            parent = saved_trend[(year, fee, slip)]
            for capital, rounding in SETTINGS:
                strategies = dict(intraday=DirectionalSweepStructureConfirmStrategy(), swing=DirectionalSwingEfficiencyStrategy())
                sleeves = [ResearchSleeve(s["name"], strategies[s["name"]], replace(
                    PerpetualResearchConfig(**s["config"]), initial_cash=capital)) for s in parent["sleeves"]]
                engine = PortfolioResearchEngine(sleeves, limits, directional_loss_guard=True, swing_failure_exit=True)
                result, rejected = trend_run(engine, rounding, candles=period, evaluation_start_ms=start,
                                             marks=[m for m in marks if start <= m.timestamp_ms < end],
                                             funding=[f for f in funding if start <= f.timestamp_ms < end])
                if capital == 10000 and result["metrics"] != parent["result"]["metrics"]:
                    raise ValueError(f"trend {year} {fee}/{slip}: parent reproduction failed")
                rows.append(dict(book="trend", year=year, cost_case=f"{fee}/{slip}", capital=capital, rounding=rounding,
                                 metrics=result["metrics"], entries=len(result["trades"]), rejected_below_minimum=rejected,
                                 min_quantity=min((t["quantity"] for t in result["trades"]), default=None)))
                print("trend", year, f"{fee}/{slip}", capital, rounding, f"{result['metrics']['total_return']:+.3%}", rejected, flush=True)
    btc = assets()["BTC"]
    for year in range(2022, 2026):
        for case, costs in CARRY_COSTS.items():
            for capital, rounding in SETTINGS:
                result, skipped = carry_run(btc, year, costs, capital, rounding)
                if capital == 10000 and result["metrics"] != saved_carry[(year, case)]:
                    raise ValueError(f"carry {year} {case}: parent reproduction failed")
                rows.append(dict(book="carry", year=year, cost_case=case, capital=capital, rounding=rounding,
                                 metrics=result["metrics"], rebalances=result["rebalances"], skipped_rebalances=skipped,
                                 liquidated_at_ms=result["liquidated_at_ms"]))
                print("carry", year, case, capital, rounding, f"{result['metrics']['total_return']:+.3%}", skipped, flush=True)

    def pick(book: str, rounding: bool) -> list[dict]:
        return [r for r in rows if r["book"] == book and r["capital"] == 3000 and r["rounding"] is rounding]
    primary = {"trend": "5/5", "carry": "primary"}
    checks = {}
    for book in ("trend", "carry"):
        base, lots = pick(book, False), pick(book, True)
        mean = lambda rs: sum(r["metrics"]["total_return"] for r in rs if r["cost_case"] == primary[book]) / 4
        dd = lambda rs: min(r["metrics"]["maximum_drawdown"] for r in rs)
        checks[book] = dict(mean_unrounded=mean(base), mean_rounded=mean(lots), worst_dd_unrounded=dd(base), worst_dd_rounded=dd(lots))
        passed = mean(lots) >= mean(base) - .005 and dd(lots) >= dd(base) - .01
        if book == "trend":
            entries = sum(r["entries"] for r in base)
            checks[book]["rejected_share"] = sum(r["rejected_below_minimum"] for r in lots) / entries
            passed = passed and checks[book]["rejected_share"] <= .15
        else:
            passed = passed and all(r["liquidated_at_ms"] is None for r in lots)
        checks[book]["passed"] = passed
    artifact = dict(schema="small_capital_lots_v1", design=str(DESIGN), development_trial=None, sealed_data_used=False,
                    exchange_rules=dict(step=STEP, perp_min_notional=PERP_MIN_NOTIONAL, source="Binance exchangeInfo 2026-10-29"),
                    source_sha256={p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES}, rows=rows, checks=checks)
    OUTPUT.write_text(json.dumps(artifact, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(checks, indent=1))


if __name__ == "__main__":
    main()
