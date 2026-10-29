"""Historical replay of the paper book with the research fill model.

This exists only to prove that the paper book makes the same decisions as
PortfolioResearchEngine; it is not forward paper evidence.
"""
from app.backtest.metrics import calculate_metrics
from app.backtest.models import EquityPoint
from app.backtest.portfolio_research import PortfolioResearchResult
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.execution.perpetual_paper import FillPrices, PaperPortfolioBook, sleeve_signals


def replay_research_fills(book: PaperPortfolioBook, candles: list[Candle], *, evaluation_start_ms: int,
                          marks: list[MarkPriceCandle], funding: list[FundingRate]) -> PortfolioResearchResult:
    start = next(iter(book.engines.values())).validate_inputs(candles, evaluation_start_ms=evaluation_start_ms,
                                                              marks=marks, funding=funding)
    curve = [EquityPoint(evaluation_start_ms - 3600000, book.initial_cash, False)]
    by_hour: dict[int, list[FundingRate]] = {}
    for event in funding:
        by_hour.setdefault(event.timestamp_ms // 3600000, []).append(event)
    for i in range(start, len(candles)):
        candle, mark = candles[i], marks[i - start]
        history = candles[:i]
        signals = sleeve_signals(book.sleeves, history)
        events = by_hour.get(candle.timestamp_ms // 3600000, [])
        at_open = FillPrices(candle.open, candle.open)
        book.open_phase(hour_ms=candle.timestamp_ms, history=history, signals=signals, trigger=candle.open,
                        prices=at_open, mark=mark.open, fill_ms=candle.timestamp_ms,
                        funding=[e for e in events if e.timestamp_ms <= candle.timestamp_ms])
        book.check_risk(hour_ms=candle.timestamp_ms, identity=candle, trade_low=candle.low, trade_high=candle.high,
            mark_low=mark.low, mark_high=mark.high,
            liquidation_reference=lambda lot, level: (min(mark.open, level) if lot.position.direction == 1
                                                      else max(mark.open, level)),
            stop_reference=lambda lot: (min(candle.open, lot.position.stop) if lot.position.direction == 1
                                        else max(candle.open, lot.position.stop)),
            fill_ms=candle.timestamp_ms, funding=[e for e in events if e.timestamp_ms > candle.timestamp_ms])
        if i == len(candles) - 1:
            book.close_all(hour_ms=candle.timestamp_ms, identity=candle, prices=FillPrices(candle.close, candle.close),
                           reason="end_of_data", fill_ms=candle.timestamp_ms)
        point = book.mark_point(candle.timestamp_ms, mark.close)
        curve.append(EquityPoint(candle.timestamp_ms, point.equity, bool(book.book)))
    if abs(book.cash - book.initial_cash - sum(t.pnl for t in book.trades)) > 1e-6:
        raise ValueError("shared account cash/PnL does not reconcile")
    metrics = calculate_metrics(curve, book.trades, book.initial_cash, "1h", book.max_ratio)
    return PortfolioResearchResult("perpetual_multi_position_portfolio", candles[0].symbol, "1h",
        book.initial_cash, book.cash, metrics, book.trades, curve, book.points, book.admissions, book.peak_positions)
