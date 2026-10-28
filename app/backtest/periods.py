from datetime import datetime, timezone

from app.backtest.models import BacktestResult


def annual_performance(result: BacktestResult) -> list[dict[str, float | int]]:
    """Attribute continuous equity returns to years without resetting positions."""
    rows: list[dict[str, float | int]] = []
    previous = result.equity_curve[0].equity
    current_year: int | None = None
    start = peak = previous
    drawdown = 0.0
    for point in result.equity_curve[1:]:
        year = datetime.fromtimestamp(point.timestamp_ms / 1000, timezone.utc).year
        if year != current_year:
            if current_year is not None:
                rows.append(dict(year=current_year, total_return=previous / start - 1,
                                 maximum_drawdown=drawdown, final_equity=previous))
            current_year = year
            start = peak = previous
            drawdown = 0.0
        peak = max(peak, point.equity)
        if peak > 0:
            drawdown = min(drawdown, point.equity / peak - 1)
        previous = point.equity
    if current_year is not None:
        rows.append(dict(year=current_year, total_return=previous / start - 1,
                         maximum_drawdown=drawdown, final_equity=previous))
    return rows
