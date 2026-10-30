"""BTC spot 50-day filter forward paper (registration: docs/research/2026-10-30-btc-trend-filter-forward-paper.md).

  step    one idempotent decision for the current UTC day (safe to schedule or rerun)
  run     loop: step every --poll seconds until stopped
  status  books, equity at the current quote, decision coverage
  parity  recompute every recorded decision with the backtest signal from Binance daily closes
Paper only: refuses to run when LIVE_TRADING=true. No orders, no keys.
"""
import argparse
from hashlib import sha256
from pathlib import Path
import time

from app.backtest.trend_filter import wants_btc
from app.data.live_perpetual import FeedError
from app.execution.filter_paper import DAY_MS, WINDOW, BinanceSpotDailyFeed, FilterPaperRunner
from scripts.paper_perpetual import require_paper_only

ROOT = Path("data/paper-filter")
SOURCES = ("app/execution/filter_paper.py", "app/backtest/trend_filter.py", "app/execution/paper_ledger.py",
           "scripts/paper_filter.py", "docs/research/2026-10-30-btc-trend-filter-forward-paper.md")


def clock() -> int:
    return int(time.time() * 1000)


def open_runner(name: str) -> FilterPaperRunner:
    runner = FilterPaperRunner(ROOT / name, BinanceSpotDailyFeed(), clock)
    hashes = {p: sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES}
    if "run" not in runner.ledger:
        runner.ledger.append("run", "run", dict(name=name, capital=runner.capital, source_sha256=hashes), clock())
    elif runner.ledger.events[0].payload["source_sha256"] != hashes:
        raise SystemExit("source files changed since this run started; start a new run name instead")
    return runner


def status(runner: FilterPaperRunner) -> None:
    quote = runner.feed.quote()
    mid = (quote.bid + quote.ask) / 2
    decisions = runner.decisions()
    print(f"decisions {len(decisions)}", f"latest hold_btc={decisions[max(decisions)]}" if decisions else "")
    for case, book in runner.books().items():
        print(f"  {case:8s} cash {book.cash:10.2f} btc {book.btc:.5f} equity {book.cash + book.btc * mid:10.2f}")
    incidents = [e for e in runner.ledger.events if e.type == "incident"]
    print(f"incidents {len(incidents)}", incidents[-1].payload if incidents else "")


def parity(runner: FilterPaperRunner) -> None:
    closes = runner.feed.closed_daily()
    mismatched = []
    for day, hold in sorted(runner.decisions().items()):
        history = [closes.get(day - k * DAY_MS) for k in range(WINDOW, 0, -1)]
        if None in history:
            print("cannot recheck", day, "(older than the feed window)")
            continue
        if wants_btc(history, WINDOW) != hold:
            mismatched.append(day)
    print("parity", "OK" if not mismatched else f"MISMATCH {mismatched}", f"({len(runner.decisions())} decisions)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("step", "run", "status", "parity"))
    parser.add_argument("--name", default="forward-1")
    parser.add_argument("--poll", type=int, default=300)
    args = parser.parse_args()
    require_paper_only()
    runner = open_runner(args.name)
    if args.command == "step":
        print(runner.step())
    elif args.command == "run":
        while True:
            try:
                print(time.strftime("%Y-%m-%d %H:%M:%S"), runner.step(), flush=True)
            except FeedError as exc:
                print(time.strftime("%Y-%m-%d %H:%M:%S"), "feed error, retrying:", exc, flush=True)
            time.sleep(args.poll)
    elif args.command == "status":
        status(runner)
    else:
        parity(runner)


if __name__ == "__main__":
    main()
