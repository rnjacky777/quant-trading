"""Daily time-series momentum sleeve screen on 2024/2025 tuning data.

Rules are fixed in docs/research/2026-10-28-daily-momentum-design.md. Hourly
mark-to-market simulation, not a PortfolioResearchEngine replay. Does not touch
the 2022/2023 validation tape.
"""
import json
from math import log, sqrt
from pathlib import Path
import statistics as st

YEARS = {2024: (1704067200000, 1735689600000), 2025: (1735689600000, 1767225600000)}
HOUR, DAY = 3600000, 86400000
LOOKBACK, VOL_DAYS, VOL_TARGET, MAX_WEIGHT = 28, 20, .20, .5
BASELINE = Path("data/perpetual-swing-failure-exit.json")
OUTPUT = Path("data/daily-momentum-research.json")


def simulate(candles: list[dict], funding: dict[int, tuple[float, float]], start: int, end: int, cost: int) -> dict:
    side_cost = 15 * cost / 1e4
    daily = {int(c["open_time"]) // DAY: float(c["close"]) for c in candles if int(c["open_time"]) % DAY == 23 * HOUR}
    cash, direction, quantity, entry = 10000.0, 0, 0.0, 0.0
    peak, drawdown, curve, trades = cash, 0.0, [], []
    gross_pnl = fees = funding_pnl = 0.0
    period = [c for c in candles if start <= int(c["open_time"]) < end]
    for index, candle in enumerate(period):
        time, price = int(candle["open_time"]), float(candle["open"])
        target = direction
        if time % DAY == 0:
            day = time // DAY - 1  # last completed daily close
            if day in daily and day - LOOKBACK in daily:
                momentum = daily[day] / daily[day - LOOKBACK] - 1
                target = 1 if momentum > 0 else -1 if momentum < 0 else direction
        if target != direction:
            if direction:
                pnl = direction * quantity * (price - entry)
                cost_paid = quantity * price * side_cost
                cash += pnl - cost_paid
                gross_pnl += pnl
                fees += cost_paid
                trades[-1].update(exit_ms=time, exit_price=price, pnl=pnl - cost_paid - trades[-1]["entry_cost"])
            returns = [log(daily[d] / daily[d - 1]) for d in range(time // DAY - VOL_DAYS, time // DAY)
                       if d in daily and d - 1 in daily]
            sigma = st.pstdev(returns) * sqrt(365)
            weight = min(MAX_WEIGHT, VOL_TARGET / sigma) if sigma else 0.
            direction, entry, quantity = target, price, weight * cash / price
            entry_cost = quantity * price * side_cost
            cash -= entry_cost
            fees += entry_cost
            trades.append(dict(direction=direction, entry_ms=time, entry_price=price, weight=weight, entry_cost=entry_cost))
        if direction and time in funding:
            rate, mark = funding[time]
            payment = -direction * quantity * mark * rate
            cash += payment
            funding_pnl += payment
            trades[-1]["funding"] = trades[-1].get("funding", 0.) + payment
        close = float(candle["close"])
        if index == len(period) - 1 and direction:
            pnl = direction * quantity * (close - entry)
            cost_paid = quantity * close * side_cost
            cash += pnl - cost_paid
            gross_pnl += pnl
            fees += cost_paid
            trades[-1].update(exit_ms=time + HOUR, exit_price=close, pnl=pnl - cost_paid - trades[-1]["entry_cost"])
            direction, quantity = 0, 0.
        worst = float(candle["low"] if direction == 1 else candle["high"]) if direction else close
        equity_worst = cash + direction * quantity * (worst - entry)
        equity = cash + direction * quantity * (close - entry)
        peak = max(peak, equity)
        drawdown = min(drawdown, equity_worst / peak - 1)
        curve.append((time + HOUR, equity))
    return dict(total_return=cash / 10000 - 1, max_drawdown=drawdown, trades=len(trades),
                gross_price_pnl=gross_pnl, fees_and_slippage=fees, funding_pnl=funding_pnl,
                long_trades=sum(t["direction"] == 1 for t in trades),
                winning_trades=sum(t.get("pnl", 0) + t.get("funding", 0) > 0 for t in trades),
                average_weight=st.mean(t["weight"] for t in trades), trade_list=trades, curve=curve)


def daily_returns(curve: list[tuple[int, float]]) -> dict[int, float]:
    closes = {t // DAY: e for t, e in curve if t % DAY == 0}
    return {d: closes[d] / closes[d - 1] - 1 for d in closes if d - 1 in closes}


def main() -> None:
    root = Path("data/btc-perpetual-1h")
    candles = json.loads((root / "klines.json").read_text())
    funding = {int(f["fundingTime"]) // HOUR * HOUR: (float(f["fundingRate"]), float(f["markPrice"]))
               for f in json.loads((root / "funding-api.json").read_text())}
    baselines = {(r["year"], r["cost_multiplier"]): r["result"]["equity_curve"]
                 for r in json.loads(BASELINE.read_text(encoding="utf-8"))["rows"]}
    rows = []
    for year, (start, end) in YEARS.items():
        for cost in (1, 2):
            result = simulate(candles, funding, start, end, cost)
            mine = daily_returns(result.pop("curve"))
            base = daily_returns([(p["timestamp_ms"] + HOUR, p["equity"]) for p in baselines[(year, cost)]])
            days = sorted(set(mine) & set(base))
            result["daily_correlation_with_baseline"] = st.correlation([mine[d] for d in days], [base[d] for d in days])
            rows.append(dict(year=year, cost_multiplier=cost) | result)
            print(year, cost, f"ret={result['total_return']*100:.2f}% dd={result['max_drawdown']*100:.2f}%",
                  f"trades={result['trades']} long={result['long_trades']} wins={result['winning_trades']}",
                  f"gross={result['gross_price_pnl']:.0f} costs={result['fees_and_slippage']:.0f}",
                  f"funding={result['funding_pnl']:.0f} w={result['average_weight']:.2f}",
                  f"corr={result['daily_correlation_with_baseline']:.2f}")
    OUTPUT.write_text(json.dumps(dict(schema="daily_momentum_screen_v1", design="docs/research/2026-10-28-daily-momentum-design.md",
        used_for_tuning=True, independent_validation=False, validation_tape_used=False, rows=rows), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
