"""Controlled spot ablation: sizing and frequency changes, no version writes."""
from dataclasses import replace
from pathlib import Path
import json

from app.backtest.engine import BacktestEngine
from app.backtest.reproduction import config_for_run, strategy_for_run
from app.backtest.results import serialize_result
from app.backtest.runs import BacktestRunRepository, _fingerprint
from app.data.repository import CandleRepository
from app.risk.regime import slow_slope_multiplier
from app.strategies.base import Action


def main() -> None:
    path = Path("data/market.sqlite3")
    repo = BacktestRunRepository(path)
    version = next(v for v in repo.list_strategy_versions() if v.strategy_family == "sma" and v.version_number == 12)
    runs = repo.list_runs_for_strategy(version.strategy_key, limit=None)
    rows = []
    diagnostics = []
    for year, since, end in ((2024, 1704067200000, 1735689600000), (2025, 1735689600000, 1767225600000)):
        run = next(r for r in runs if r.since_ms == since and r.until_ms == end - 14400000)
        tape = CandleRepository(path).list_range("binance", "BTC/USDT", "4h", since - 180 * 14400000, end)
        if len(tape) != (end - since) // 14400000 + 180:
            raise ValueError("incomplete annual tape")
        for mode, regime, slow in (("V12", "fixed", 180), ("risk_only", "slow_slope", 180),
                                   ("frequency_only", "fixed", 90), ("combined", "slow_slope", 90)):
            for cost in (1, 2):
                base = config_for_run(run)
                config = replace(base, risk_regime=regime, fee_bps=base.fee_bps * cost, slippage_bps=base.slippage_bps * cost)
                strategy = strategy_for_run(run, config, slow=slow)
                result = BacktestEngine(config).run(tape, strategy, evaluation_start_ms=since)
                rows.append(dict(year=year, mode=mode, costs=cost, fingerprint=_fingerprint(tape),
                                 result=json.loads(serialize_result(result))))
                if cost == 1:
                    signals = [(tape[i].timestamp_ms, strategy.generate(tape[:i]).action,
                                slow_slope_multiplier(tape[:i], 180)) for i in range(180, len(tape))]
                    invested = lambda t: any(x.entry_timestamp_ms <= t <= x.exit_timestamp_ms for x in result.trades)
                    blocked, blocked_buy, flat_buy = False, 0, 0
                    exits = {x.exit_timestamp_ms: x for x in result.trades}
                    for t, action, _ in signals:
                        if action is Action.SELL:
                            blocked = False
                        if action is Action.BUY and not invested(t):
                            flat_buy += 1
                            blocked_buy += int(blocked)
                        if t in exits and exits[t].exit_reason in {"stop_loss", "trailing_stop"}:
                            blocked = True
                    diagnostics.append(dict(year=year, mode=mode, buy_signal_bars=sum(a is Action.BUY for _, a, _ in signals),
                        flat_buy_bars=flat_buy, blocked_buy_bars=blocked_buy,
                        reduced_risk_entries=sum(slow_slope_multiplier(tape[:next(i for i,c in enumerate(tape) if c.timestamp_ms == x.entry_timestamp_ms)], 180) == .5 for x in result.trades),
                        exit_reasons=[x.exit_reason for x in result.trades]))
                print(year, mode, cost, result.metrics.total_return, result.metrics.number_of_trades, flush=True)
    Path("data/trade-frequency-research.json").write_text(json.dumps(dict(
        market="BTC spot 4h, long/cash, leverage 1, max entry risk 0.5%", rows=rows,
        diagnostics=diagnostics, validation="All periods used for tuning, no unseen claim"), allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
