"""Forward paper tooling for the frozen BTC perpetual baseline.

  parity    replay the paper book on 2024/2025 tuning data and require snapshot
            equality with PortfolioResearchEngine (decision parity, not evidence)
  rehearse  engineering rehearsal on live public data; never performance evidence
  status    verify a run ledger, replay it and print books, incidents and checks

Formal activation is intentionally absent until the registered gates pass.
"""
import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.config.settings import Settings
from app.data.live_perpetual import BinanceUsdmPublicFeed, FeedError
from app.execution.paper_replay import replay_research_fills
from app.execution.paper_runner import (COST_CASES, HOUR_MS, STRATEGIES, PaperRunner, RunConfig, SystemClock,
                                        frozen_books, frozen_carry_books, source_hashes)
from app.execution.perpetual_paper import PaperPortfolioBook
from app.monitoring.paper_checks import reconcile, stop_breach, StopRule
from app.portfolio.research_risk import PortfolioLimits
from scripts.research_perpetual_directions import fingerprint
from scripts.research_risk_budget import late_inputs

MANIFEST = Path("docs/research/2026-10-29-forward-paper-manifest.json")
ROOT = Path("data/paper-perpetual")


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def require_paper_only() -> None:
    if Settings.from_env().live_trading:
        raise SystemExit("LIVE_TRADING=true: paper tooling refuses to run next to a live-enabled environment")


def git_state() -> dict:
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    return dict(git_head=head, dirty=bool(dirty))


def parity() -> None:
    m = manifest()
    tape, marks, funding = late_inputs()
    rows = []
    for year in (2024, 2025):
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        period = [c for c in tape if start - 243 * HOUR_MS <= c.timestamp_ms < end]
        pm = [x for x in marks if start <= x.timestamp_ms < end]
        rates = [f for f in funding if start <= f.timestamp_ms < end]
        for fee, slip in COST_CASES:
            def sleeves() -> list[ResearchSleeve]:
                return [ResearchSleeve(s["name"], STRATEGIES[s["strategy"]](), replace(
                    PerpetualResearchConfig(**s["config"]), fee_bps=fee, slippage_bps=slip)) for s in m["sleeves"]]
            limits = PortfolioLimits(**m["portfolio_limits"])
            research = serialize_result(PortfolioResearchEngine(sleeves(), limits, directional_loss_guard=True,
                swing_failure_exit=True).run(period, evaluation_start_ms=start, marks=pm, funding=rates))
            paper = serialize_result(replay_research_fills(PaperPortfolioBook(sleeves(), limits), period,
                evaluation_start_ms=start, marks=pm, funding=rates))
            metrics = json.loads(research)["metrics"]
            rows.append(dict(year=year, fee_bps=fee, slippage_bps=slip, snapshot_equal=research == paper,
                             research_sha256=sha256(research.encode()).hexdigest(),
                             paper_sha256=sha256(paper.encode()).hexdigest(),
                             total_return=metrics["total_return"], trades=metrics["number_of_trades"],
                             input_fingerprints=dict(candles=fingerprint([asdict(c) for c in period]),
                                                     marks=fingerprint([asdict(x) for x in pm]),
                                                     funding=fingerprint([asdict(f) for f in rates]))))
            print(year, f"{fee}/{slip}", "equal" if rows[-1]["snapshot_equal"] else "DIFFERENT",
                  f"return={metrics['total_return']:.6%}", f"trades={metrics['number_of_trades']}", flush=True)
    out = ROOT / f"parity-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(schema="paper_decision_parity_v1", purpose="decision parity; tuning data, not evidence",
        manifest_sha256=sha256(MANIFEST.read_bytes()).hexdigest(), paper_source_sha256=source_hashes(),
        passed=all(r["snapshot_equal"] for r in rows), rows=rows, **git_state()), indent=1), encoding="utf-8")
    print("saved", out, "passed" if all(r["snapshot_equal"] for r in rows) else "FAILED")


def rehearse(hours: int, resume: str | None) -> None:
    require_paper_only()
    clock = SystemClock()
    if resume:
        run_dir = ROOT / resume
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    else:
        start = (clock.now_ms() // HOUR_MS + 1) * HOUR_MS
        run_id = f"rehearsal-{datetime.fromtimestamp(start / 1000, timezone.utc):%Y%m%dT%H}Z"
        run_dir = ROOT / run_id
        if run_dir.exists():
            raise SystemExit(f"{run_dir} exists; use --resume {run_id}")
        meta = dict(run_id=run_id, mode="rehearsal", start_ms=start, end_ms=start + hours * HOUR_MS,
                    note="engineering rehearsal only; results are not performance evidence", **git_state())
        run_dir.mkdir(parents=True)
        (run_dir / "run.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    config = RunConfig(meta["run_id"], "rehearsal", meta["start_ms"], meta["end_ms"])
    print(f"rehearsal {config.run_id}: {datetime.fromtimestamp(config.start_ms / 1000, timezone.utc)} -> "
          f"{datetime.fromtimestamp(config.end_ms / 1000, timezone.utc)} UTC, ledger {run_dir / 'events.jsonl'}", flush=True)
    result = PaperRunner(run_dir, BinanceUsdmPublicFeed(), clock, manifest(), config).run()
    print("finished", result["reason"])


class OfflineFeed:
    def __getattr__(self, name: str):
        def unavailable(*args, **kwargs):
            raise FeedError("status is offline")
        return unavailable


def status(run_dir: Path) -> None:
    meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    config = RunConfig(meta["run_id"], meta["mode"], meta["start_ms"], meta["end_ms"])
    recorded = json.loads((run_dir / "events.jsonl").open(encoding="utf-8").readline())["payload"]
    try:
        runner = PaperRunner(run_dir, OfflineFeed(), SystemClock(), manifest(), config)
    except ValueError as exc:
        if "run identity" not in str(exc):
            raise
        # Older runs were recorded by different paper code: replay read-only and say so.
        print("WARNING: paper source or config changed since this run started; read-only replay with current code")
        carry = {k: v for k, v in frozen_carry_books().items() if k in recorded.get("carry_cases", [])}
        runner = PaperRunner(run_dir, OfflineFeed(), SystemClock(), manifest(), config, carry_books=carry,
                             books=frozen_books(manifest()), verify_identity=False)
    hours = (min(SystemClock().now_ms(), config.end_ms) - config.start_ms) // HOUR_MS
    kinds: dict[str, int] = {}
    for incident in runner.incidents:
        kinds[incident["kind"]] = kinds.get(incident["kind"], 0) + 1
    print(f"{meta['run_id']} ({meta['mode']}): ledger events={len(runner.ledger.events)} chain=verified")
    print(f"hours elapsed={max(hours, 0)} decided={len(runner.decided)} closed={len(runner.closed)} "
          f"terminated={runner.terminated['reason'] if runner.terminated else 'no'}")
    print("incidents:", kinds or "none")
    marks = [e.payload["mark_close"] for e in runner.ledger.events if e.type == "hour_close"]
    for name, book in runner.books.items():
        last = book.points[-1] if book.points else None
        issues = reconcile(book, marks[-1]) if marks else []
        equity = last.equity if last else book.cash
        print(f"  {name}: equity={equity:.2f} return={equity / book.initial_cash - 1:+.4%} trades={len(book.trades)} "
              f"open={len(book.book)} fees={sum(t.fees for t in book.trades):.2f} "
              f"funding={sum(t.funding for t in book.trades):.2f} stop_rule={stop_breach(book, StopRule()) or 'ok'} "
              f"reconcile={'ok' if not issues else issues}")
    for name, carry in runner.carry_books.items():
        equity = carry.points[-1][1] if carry.points else carry.initial_cash
        b = carry.book
        print(f"  {name}: equity={equity:.2f} return={equity / carry.initial_cash - 1:+.4%} "
              f"rebalances={len(b.rebalances)} funding={b.funding:.2f} fees={b.fees:.2f} slippage={b.slippage:.2f} "
              f"liquidated={'yes' if carry.liquidated_at else 'no'} hedge={'ok' if not carry.hedge_issues() else carry.hedge_issues()}")
    for cost, book in runner.books.items():
        carry = runner.carry_books.get(f"carry_f043_drift5:{cost}")
        if carry is None or not book.points or not carry.points:
            continue
        combined = book.points[-1].equity + carry.points[-1][1] - book.initial_cash
        print(f"  combined trend+carry_f043_drift5 {cost}: equity={combined:.2f} "
              f"return={combined / book.initial_cash - 1:+.4%} (additive, as in experiment 3)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("parity")
    r = sub.add_parser("rehearse")
    r.add_argument("--hours", type=int, default=72)
    r.add_argument("--resume")
    s = sub.add_parser("status")
    s.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "parity":
        parity()
    elif args.command == "rehearse":
        rehearse(args.hours, args.resume)
    else:
        status(args.run_dir)


if __name__ == "__main__":
    main()
