"""Forward paper runner: public data -> completed bars -> frozen signals -> four cost books.

Every state change is a ledger event applied by the same code path live and on
restart, so recovery replays recorded decisions instead of deciding again. No
exchange order path exists; quotes only price simulated fills.
"""
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Protocol

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import ResearchSleeve
from app.data.live_perpetual import FeedError, MarkSnapshot, PerpetualFeed, Quote
from app.data.models import Candle, FundingRate
from app.execution.paper_ledger import PaperLedger
from app.execution.perpetual_paper import FillPrices, PaperPortfolioBook, sleeve_signals
from app.monitoring.paper_checks import DataQualityLimits, StopRule, quote_issues, reconcile, stop_breach
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy

HOUR_MS = 3600000
FUNDING_INTERVAL_MS = 8 * HOUR_MS
WARMUP_HOURS = 243
COST_CASES = ((5, 5), (10, 5), (10, 10), (20, 10))
PRIMARY = "5/5"
PAPER_SOURCES = ("app/execution/perpetual_paper.py", "app/execution/paper_ledger.py",
                 "app/execution/paper_runner.py", "app/data/live_perpetual.py", "app/monitoring/paper_checks.py",
                 "app/backtest/portfolio_research.py", "app/backtest/long_short_research.py",
                 "app/portfolio/research_risk.py", "app/risk/regime.py", "app/risk/sizing.py",
                 "app/strategies/sweep_structure_confirm.py", "app/strategies/swing_efficiency.py",
                 "app/strategies/swing_failure.py", "app/data/aggregation.py")
STRATEGIES = {"perpetual_sweep_past_3bar_structure_confirmation": DirectionalSweepStructureConfirmStrategy,
              "perpetual_swing_confirmation_er20_ge_03": DirectionalSwingEfficiencyStrategy}


class Clock(Protocol):
    def now_ms(self) -> int: ...
    def sleep(self, seconds: float) -> None: ...


class SystemClock:
    def now_ms(self) -> int:
        return int(time.time() * 1000)

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


@dataclass(frozen=True)
class RunConfig:
    run_id: str
    mode: str
    start_ms: int
    end_ms: int
    poll_seconds: float = 5
    # Waiting past the 60s latency limit lets late bars still drive exits; entries stay blocked.
    bar_wait_ms: int = 120000
    funding_wait_ms: int = 120000

    def __post_init__(self) -> None:
        if self.mode not in {"rehearsal", "formal"}:
            raise ValueError("paper mode must be rehearsal or formal")
        if self.start_ms % HOUR_MS or self.end_ms % HOUR_MS or self.end_ms <= self.start_ms:
            raise ValueError("paper window must be whole UTC hours")


def frozen_books(manifest: dict) -> dict[str, PaperPortfolioBook]:
    """Four independent cost books from the frozen manifest; strategy parameters are untouched."""
    flags = manifest["engine_flags"]
    if not (flags["directional_loss_guard"] and flags["swing_failure_exit"]) or any(
            v for k, v in flags.items() if k not in {"directional_loss_guard", "swing_failure_exit"}):
        raise ValueError("paper book supports only the frozen baseline flags")
    books = {}
    for fee, slip in COST_CASES:
        sleeves = [ResearchSleeve(s["name"], STRATEGIES[s["strategy"]](), replace(
            PerpetualResearchConfig(**s["config"]), fee_bps=fee, slippage_bps=slip)) for s in manifest["sleeves"]]
        books[f"{fee}/{slip}"] = PaperPortfolioBook(sleeves, PortfolioLimits(**manifest["portfolio_limits"]))
    return books


def source_hashes(root: Path = Path(".")) -> dict[str, str]:
    return {p: sha256((root / p).read_bytes()).hexdigest() for p in PAPER_SOURCES}


class PaperRunner:
    def __init__(self, run_dir: Path, feed: PerpetualFeed, clock: Clock, manifest: dict, config: RunConfig,
                 *, quality: DataQualityLimits = DataQualityLimits(), rule: StopRule = StopRule(),
                 hashes: Callable[[], dict[str, str]] = source_hashes,
                 books: dict[str, PaperPortfolioBook] | None = None) -> None:
        self.feed, self.clock, self.config, self.quality, self.rule = feed, clock, config, quality, rule
        # Tests inject books; a real run always uses the frozen manifest.
        self.books = books if books is not None else frozen_books(manifest)
        if PRIMARY not in self.books:
            raise ValueError("primary 5/5 cost book required")
        self.meta = dict(run_id=config.run_id, mode=config.mode, start_ms=config.start_ms, end_ms=config.end_ms,
                         manifest_sha256=sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
                         paper_source_sha256=hashes(), quality=asdict(quality), stop_rule=asdict(rule),
                         cost_cases=list(self.books), primary=PRIMARY,
                         fill_model="first quote after decision: buy ask / sell bid, then adverse slippage bps")
        self.bars: dict[int, Candle] = {}
        self.bar_received: dict[int, int] = {}
        self.funding: dict[int, FundingRate] = {}
        self.provisional_funding: set[int] = set()
        self.incidents: list[dict] = []
        self.entry_block: set[str] = set()
        self.decided: set[int] = set()
        self.closed: set[int] = set()
        self.terminated: dict | None = None
        self.ledger = PaperLedger(run_dir / "events.jsonl")
        for event in self.ledger.events:
            self._apply(event.type, event.payload)
        self.marks: list[float] = []
        self.trades_seen: list[float] = []
        self.pre_settlement: dict[int, MarkSnapshot] = {}

    # ---- event application (shared by live path and restart replay) ----
    def _apply(self, type_: str, p: dict) -> None:
        if type_ == "run":
            if {k: p[k] for k in self.meta} != self.meta:
                raise ValueError("run identity, config or paper source changed; start a new registered run")
        elif type_ == "bar":
            self.bars[p["candle"]["timestamp_ms"]] = Candle(**p["candle"])
            self.bar_received[p["candle"]["timestamp_ms"]] = p["received_ms"]
        elif type_ == "funding":
            self.funding[p["timestamp_ms"]] = FundingRate(p["exchange"], p["symbol"], p["timestamp_ms"], p["rate"], p["mark_price"])
            if p["provisional"]:
                self.provisional_funding.add(p["timestamp_ms"])
        elif type_ == "decision":
            self._apply_decision(p)
        elif type_ == "tick":
            self._apply_tick(p)
        elif type_ == "hour_close":
            self._apply_close(p)
        elif type_ == "incident":
            self.incidents.append(p)
            if p.get("blocks_entries"):
                self.entry_block.add(p["kind"])
        elif type_ == "terminated":
            self._apply_termination(p)
        else:
            raise ValueError(f"unknown paper event {type_}")

    def _history(self, hour_ms: int) -> list[Candle]:
        history, ts = [], hour_ms - HOUR_MS
        while ts in self.bars:
            history.append(self.bars[ts])
            ts -= HOUR_MS
        return history[::-1]

    def _identity(self) -> Candle:
        return self.bars[max(self.bars)]

    def _apply_decision(self, p: dict) -> None:
        hour = p["hour_ms"]
        events = [self.funding[ts] for ts in p["funding_ts"]]
        quote = Quote(**p["quote"]) if p["quote"] else None
        for book in self.books.values():
            if p["signals_available"] and quote is not None:
                history = self._history(hour)
                book.open_phase(hour_ms=hour, history=history, signals=sleeve_signals(book.sleeves, history),
                                trigger=quote.last, prices=FillPrices(quote.ask, quote.bid), mark=p["mark"],
                                fill_ms=quote.received_ms, funding=events, allow_entries=p["allow_entries"])
            else:
                book.settle_funding(events)
        self.decided.add(hour)

    def _apply_tick(self, p: dict) -> None:
        quote, mark = Quote(**p["quote"]), p["mark"]
        prices = FillPrices(quote.ask, quote.bid)
        for book in self.books.values():
            book.check_risk(hour_ms=p["hour_ms"], identity=self._identity(), trade_low=quote.last, trade_high=quote.last,
                            mark_low=mark, mark_high=mark, liquidation_reference=lambda lot, level: mark,
                            stop_reference=lambda lot: prices.closing(lot.position.direction), fill_ms=quote.received_ms)

    def _apply_close(self, p: dict) -> None:
        events = [self.funding[ts] for ts in p["funding_ts"]]
        for book in self.books.values():
            book.settle_funding(events)
            book.observe_margin(p["mark_low"], p["mark_high"])
            book.mark_point(p["hour_ms"], p["mark_close"])
        self.closed.add(p["hour_ms"])

    def _apply_termination(self, p: dict) -> None:
        if p["quote"] is not None:
            quote = Quote(**p["quote"])
            for book in self.books.values():
                book.close_all(hour_ms=p["hour_ms"], identity=self._identity(), prices=FillPrices(quote.ask, quote.bid),
                               reason=p["reason"], fill_ms=quote.received_ms)
                book.mark_point(p["hour_ms"], p["mark"])
        self.terminated = p

    def _record(self, type_: str, event_id: str, payload: dict) -> bool:
        event = self.ledger.append(type_, event_id, payload, self.clock.now_ms())
        if event is not None:
            self._apply(type_, payload)
        return event is not None

    def _incident(self, kind: str, key: str, detail: dict, *, blocks_entries: bool = False) -> None:
        self._record("incident", f"incident:{kind}:{key}", dict(kind=kind, key=key, utc_ms=self.clock.now_ms(),
                     blocks_entries=blocks_entries, **detail))

    # ---- live data collection ----
    def _ingest_bars(self, since_ms: int) -> None:
        for candle, received in self.feed.closed_hourly(since_ms):
            ts = candle.timestamp_ms
            if ts in self.bars:
                if self.bars[ts] != candle:
                    self._incident("bar_revised", str(ts), dict(recorded=asdict(self.bars[ts]), fetched=asdict(candle)))
                continue
            if ts < self.config.start_ms - WARMUP_HOURS * HOUR_MS:
                continue
            self._record("bar", f"bar:{ts}", dict(candle=asdict(candle), received_ms=received,
                         warmup=ts < self.config.start_ms))

    def _await_bar(self, hour: int) -> None:
        deadline = hour + self.config.bar_wait_ms
        while True:
            try:
                self._ingest_bars(hour - 6 * HOUR_MS)
            except FeedError as exc:
                self._incident("bar_fetch_failed", f"{hour}:{self.clock.now_ms()}", dict(error=str(exc)))
            if hour - HOUR_MS in self.bars or self.clock.now_ms() >= deadline:
                return
            self.clock.sleep(2)

    def _collect_funding(self, hour: int) -> None:
        if hour % FUNDING_INTERVAL_MS or hour in self.funding:
            return
        deadline = hour + self.config.funding_wait_ms
        while True:
            try:
                for event in self.feed.funding(hour - HOUR_MS, hour + HOUR_MS - 1):
                    if event.timestamp_ms not in self.funding and hour - HOUR_MS < event.timestamp_ms < hour + HOUR_MS:
                        self._record("funding", f"funding:{event.timestamp_ms}", dict(asdict(event), provisional=False))
            except FeedError as exc:
                self._incident("funding_fetch_failed", f"{hour}:{self.clock.now_ms()}", dict(error=str(exc)))
            if any(abs(ts - hour) < HOUR_MS for ts in self.funding) or self.clock.now_ms() >= deadline:
                break
            self.clock.sleep(5)
        if not any(abs(ts - hour) < HOUR_MS for ts in self.funding):
            # Never treat missing funding as zero: use the pre-settlement published rate and flag it.
            snap = self.pre_settlement.get(hour)
            if snap is None:
                self._incident("funding_unavailable", str(hour), {}, blocks_entries=False)
                return
            self._record("funding", f"funding:{hour}", dict(exchange="binance-usdm", symbol="BTC/USDT", timestamp_ms=hour,
                         rate=snap.funding_rate, mark_price=snap.mark, provisional=True))
            self._incident("funding_provisional", str(hour), dict(rate=snap.funding_rate, mark=snap.mark))

    def _mark(self) -> MarkSnapshot:
        snap = self.feed.mark()
        # Keep the latest published rate before each settlement as the flagged fallback.
        if snap.exchange_ms < snap.next_funding_ms:
            self.pre_settlement[snap.next_funding_ms] = snap
        return snap

    def _due_funding(self, low: int, high: int) -> list[int]:
        applied = self.books[PRIMARY].applied_funding
        return sorted(ts for ts in self.funding if low < ts <= high and ts not in applied)

    def _decide(self, hour: int) -> None:
        if hour in self.decided:
            return
        reasons = []
        bar = self.bars.get(hour - HOUR_MS)
        history = self._history(hour)
        if bar is None:
            reasons.append("bar_missing")
        elif self.bar_received[hour - HOUR_MS] - hour > self.quality.bar_latency_ms:
            reasons.append("bar_late")
        signals_available = bar is not None and len(history) >= WARMUP_HOURS
        if bar is not None and not signals_available:
            reasons.append("history_incomplete")
        if signals_available:
            sleeve_signals(self.books[PRIMARY].sleeves, history)
        decision_ms = self.clock.now_ms()
        try:
            skew = abs(self.feed.server_time() - self.clock.now_ms())
            if skew > self.quality.clock_skew_ms:
                reasons.append("clock_skew")
        except FeedError:
            reasons.append("server_time_unavailable")
        quote, mark = None, None
        try:
            quote = self.feed.quote()
            reasons += quote_issues(quote, decision_ms, self.quality)
        except FeedError:
            reasons.append("quote_unavailable")
        try:
            mark = self._mark().mark
        except FeedError:
            reasons.append("mark_unavailable")
        if mark is None and quote is not None:
            mark = quote.last
        reasons += sorted(self.entry_block)
        self._record("decision", f"decision:{hour}", dict(hour_ms=hour, decision_ms=decision_ms,
            signals_available=signals_available and quote is not None, allow_entries=not reasons,
            block_reasons=reasons, quote=asdict(quote) if quote else None, mark=mark,
            funding_ts=self._due_funding(-1, hour)))
        if reasons:
            self._incident("entries_blocked", str(hour), dict(reasons=reasons))

    def _poll_until(self, boundary: int, hour: int) -> None:
        failures = 0
        while self.clock.now_ms() < boundary:
            try:
                quote, snap = self.feed.quote(), self._mark()
                self.trades_seen.append(quote.last)
                self.marks.append(snap.mark)
                if hour in self.decided and any(b.risk_triggered(quote.last, snap.mark) for b in self.books.values()):
                    self._record("tick", f"tick:{hour}:{quote.received_ms}", dict(hour_ms=hour, quote=asdict(quote), mark=snap.mark))
            except FeedError as exc:
                failures += 1
                if failures == 1:
                    self._incident("quote_gap", str(hour), dict(error=str(exc)))
            self.clock.sleep(self.config.poll_seconds)

    def _close_hour(self, hour: int) -> None:
        if hour in self.closed or hour not in self.decided:
            return
        try:
            self.marks.append(self._mark().mark)
        except FeedError:
            pass
        if not self.marks:
            self._incident("valuation_gap", str(hour), {})
            return
        mark_close = self.marks[-1]
        self._record("hour_close", f"close:{hour}", dict(hour_ms=hour, mark_close=mark_close,
            mark_low=min(self.marks), mark_high=max(self.marks), observations=len(self.marks),
            funding_ts=self._due_funding(hour, hour + HOUR_MS - 1)))
        self.marks, self.trades_seen = [], []
        for name, book in self.books.items():
            issues = reconcile(book, mark_close)
            if issues:
                self._incident("reconciliation", f"{hour}:{name}", dict(book=name, issues=issues), blocks_entries=True)
        breaches = {name: stop_breach(book, self.rule) for name, book in self.books.items()}
        breached = {k: v for k, v in breaches.items() if v}
        if breached:
            self._terminate(hour + HOUR_MS, "research_stop", dict(breaches=breached))

    def _terminate(self, hour: int, reason: str, detail: dict) -> None:
        quote, mark = None, None
        for _ in range(3):
            try:
                quote = self.feed.quote()
                mark = self.feed.mark().mark
                break
            except FeedError:
                self.clock.sleep(self.config.poll_seconds)
        self._record("terminated", "terminated", dict(hour_ms=hour, reason=reason, quote=asdict(quote) if quote else None,
                     mark=mark, **detail))

    # ---- main loop ----
    def run(self) -> dict:
        if "run" not in self.ledger:
            self._record("run", "run", self.meta)
        if self.terminated:
            return self.terminated
        while self.clock.now_ms() < self.config.start_ms - self.config.poll_seconds * 1000:
            self.clock.sleep(min(60, (self.config.start_ms - self.clock.now_ms()) / 1000))
        if len(self._history(self.config.start_ms)) < WARMUP_HOURS:
            self._ingest_bars(self.config.start_ms - WARMUP_HOURS * HOUR_MS)
        while self.terminated is None:
            now = self.clock.now_ms()
            current = max(self.config.start_ms, now // HOUR_MS * HOUR_MS)
            last = max(self.decided, default=None)
            if last is not None and last < current:
                self._close_hour(last)
                if self.terminated is not None:
                    break
            # Hours without a decision are recorded as incidents, never backfilled.
            first_missing = self.config.start_ms if last is None else last + HOUR_MS
            for missed in range(first_missing, min(current, self.config.end_ms), HOUR_MS):
                self._incident("missed_hour", str(missed), dict(reason="runner_not_running"))
            if current >= self.config.end_ms:
                if last is not None:
                    self._close_hour(last)
                if self.terminated is None:
                    self._terminate(self.config.end_ms, "end_of_window", {})
                break
            if current not in self.decided:
                self._await_bar(current)
                self._collect_funding(current)
                self._decide(current)
            self._poll_until(current + HOUR_MS, current)
            self._close_hour(current)
        return self.terminated
