"""Registered data-quality, reconciliation and stop checks for forward paper runs."""
from dataclasses import dataclass

from app.data.live_perpetual import Quote
from app.execution.perpetual_paper import PaperPortfolioBook

RECONCILE_TOLERANCE = 1e-6


@dataclass(frozen=True)
class DataQualityLimits:
    """Engineering admission thresholds from the forward paper plan §3.3."""
    bar_latency_ms: int = 60000
    quote_after_decision_ms: int = 5000
    quote_staleness_ms: int = 5000
    clock_skew_ms: int = 1000


@dataclass(frozen=True)
class StopRule:
    """Registered research termination: any cost book at <=-3% return or >=10% drawdown."""
    minimum_return: float = -.03
    maximum_drawdown: float = .10


def quote_issues(quote: Quote, decision_ms: int, limits: DataQualityLimits) -> list[str]:
    issues = []
    if quote.received_ms - decision_ms > limits.quote_after_decision_ms:
        issues.append("quote_late_after_decision")
    if quote.received_ms < decision_ms:
        issues.append("quote_before_decision")
    if abs(quote.received_ms - quote.exchange_ms) > limits.quote_staleness_ms:
        issues.append("quote_stale")
    if quote.last_ms and abs(quote.received_ms - quote.last_ms) > limits.quote_staleness_ms:
        issues.append("last_trade_stale")
    if not 0 < quote.bid <= quote.ask:
        issues.append("quote_crossed")
    return issues


def reconcile(book: PaperPortfolioBook, mark: float) -> list[str]:
    """cash = initial + closed PnL + open (funding - entry fee); equity = cash + unrealized."""
    issues = []
    expected_cash = book.initial_cash + sum(t.pnl for t in book.trades) + sum(
        l.position.funding - l.position.entry_fee for l in book.book.values())
    if abs(book.cash - expected_cash) > RECONCILE_TOLERANCE:
        issues.append(f"cash_mismatch:{book.cash - expected_cash:.9f}")
    unrealized = sum(l.position.direction * l.position.quantity * (mark - l.position.entry_price)
                     for l in book.book.values())
    if abs(book.equity(mark) - book.cash - unrealized) > RECONCILE_TOLERANCE:
        issues.append("equity_mismatch")
    ids = [t.position_id for t in book.trades] + list(book.book)
    if len(ids) != len(set(ids)):
        issues.append("duplicate_position_id")
    if any(count > book.limits.daily_entries for count in book.counts.values()):
        issues.append("daily_entry_limit_exceeded")
    return issues


def stop_breach(book: PaperPortfolioBook, rule: StopRule) -> str | None:
    peak = book.initial_cash
    for point in book.points:
        peak = max(peak, point.equity)
        if point.equity / book.initial_cash - 1 <= rule.minimum_return:
            return "cumulative_return_floor"
        if 1 - point.equity / peak >= rule.maximum_drawdown:
            return "maximum_drawdown"
    return None
