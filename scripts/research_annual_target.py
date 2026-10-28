"""Fixed research screen for a 15% net return in BOTH 2024 and 2025.

No parameter search, version creation, exchange orders, or synthetic leverage.
"""
import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
from math import ceil
from pathlib import Path
from statistics import mean, pstdev

from app.backtest.configuration import make_strategy
from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.backtest.reproduction import config_for_run, strategy_for_run
from app.backtest.results import serialize_result
from app.backtest.runs import BacktestRunRepository, _fingerprint
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository
from app.strategies.base import Action, Signal, Strategy


def atr14(candles: list[Candle]) -> float | None:
    """Simple mean of 14 true ranges, not Wilder's recursive ATR."""
    if len(candles) < 15:
        return None
    return mean(max(current.high-current.low, abs(current.high-previous.close),
                    abs(current.low-previous.close))
                for previous, current in zip(candles[-15:-1], candles[-14:]))


class BollingerAtr:
    name = "research_bollinger_20_2_atr14_2"

    def generate(self, candles: list[Candle]) -> Signal:
        point = candles[-1]
        action, stop = Action.HOLD, None
        if len(candles) >= 20:
            prices = [item.close for item in candles[-20:]]
            center, deviation = mean(prices), pstdev(prices)
            atr = atr14(candles)
            if deviation > 0 and point.close < center-2*deviation and atr and point.close > 2*atr:
                action, stop = Action.BUY, point.close-2*atr
            elif point.close >= center:
                action = Action.SELL
        return Signal(point.symbol, datetime.fromtimestamp(point.timestamp_ms/1000, timezone.utc),
                      action, float(action != Action.HOLD), self.name, stop_loss_price=stop)


class AtrProtection:
    def __init__(self, strategy: Strategy) -> None:
        self.strategy = strategy
        self.name = "research_sma_atr14_2"

    def generate(self, candles: list[Candle]) -> Signal:
        signal = self.strategy.generate(candles)
        atr = atr14(candles)
        if signal.action is Action.BUY:
            if atr is None or candles[-1].close <= 2*atr:
                return replace(signal, strategy_name=self.name, action=Action.HOLD,
                               stop_loss_price=None, stop_loss_fraction=None)
            return replace(signal, strategy_name=self.name,
                           stop_loss_price=candles[-1].close-2*atr, stop_loss_fraction=None)
        return replace(signal, strategy_name=self.name)


class DonchianMidpoint:
    """20-day close channel; ratcheting midpoint exit, next-open execution.

    Cache verifies the ENTIRE previously seen prefix, so changed or shortened
    history resets state. A fresh strategy is used for every independent run.
    This is a single-horizon adaptation, not the cited portfolio replication.
    """
    name = "research_donchian_close_120_midpoint"

    def __init__(self) -> None:
        self._seen: tuple[Candle, ...] = ()
        self._long = False
        self._stop: float | None = None

    def generate(self, candles: list[Candle]) -> Signal:
        current = tuple(candles)
        if len(current) < len(self._seen) or current[:len(self._seen)] != self._seen:
            self._seen, self._long, self._stop = (), False, None
        for index in range(len(self._seen), len(current)):
            if index < 120:
                continue
            close = current[index].close
            previous = [item.close for item in current[index-120:index]]
            channel = [item.close for item in current[index-119:index+1]]
            midpoint = (max(channel)+min(channel))/2
            if self._long:
                if close <= self._stop:
                    self._long, self._stop = False, None
                else:
                    self._stop = max(self._stop, midpoint)
            elif close > max(previous):
                self._long, self._stop = True, midpoint
        self._seen = current
        point = current[-1]
        action = Action.HOLD if len(current) < 121 else Action.BUY if self._long else Action.SELL
        return Signal(point.symbol, datetime.fromtimestamp(point.timestamp_ms/1000, timezone.utc),
                      action, float(action != Action.HOLD), self.name,
                      stop_loss_price=self._stop if action is Action.BUY else None)


class RecordedSignals:
    def __init__(self, strategy: Strategy) -> None:
        self.strategy, self.name = strategy, strategy.name
        self.signals: dict[int, Signal] = {}

    def generate(self, candles: list[Candle]) -> Signal:
        signal = self.strategy.generate(candles)
        self.signals[candles[-1].timestamp_ms] = signal
        return signal


def leverage_audit(result, config: BacktestConfig, recorded: RecordedSignals) -> list[dict]:
    """Explain every executed spot trade; proposed leverage is NOT backtested."""
    equity = result.initial_cash
    rows = []
    for trade in result.trades:
        signal = recorded.signals[trade.entry_timestamp_ms-TIMEFRAMES_MS[result.timeframe]]
        initial_stop = signal.stop_loss_price or trade.entry_price*(1-(signal.stop_loss_fraction or config.stop_loss_pct))
        stop_fill = initial_stop*(1-config.slippage_bps/10000)
        loss_per_unit = trade.entry_price-stop_fill + config.fee_bps/10000*(trade.entry_price+stop_fill)
        risk_budget = equity*config.risk_per_trade
        desired_notional = risk_budget/loss_per_unit*trade.entry_price
        required = max(1, ceil(desired_notional/equity))
        actual_notional = trade.quantity*trade.entry_price
        rows.append(dict(entry_timestamp_ms=trade.entry_timestamp_ms, equity_before_entry=equity,
                         initial_stop=initial_stop, planned_risk=trade.planned_risk,
                         risk_budget=risk_budget, actual_notional=actual_notional,
                         actual_exposure=actual_notional/equity, simulated_leverage=1,
                         uncapped_risk_sized_notional=desired_notional,
                         minimum_integer_leverage_for_uncapped_size=required,
                         reason=("1x suffices: risk-sized notional is within account equity."
                                 if required == 1 else "Spot size was capped. More leverage would need verified perpetual funding, marks and margin rules; not simulated or approved here.")))
        equity += trade.pnl
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/market.sqlite3"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = BacktestRunRepository(args.db)
    versions = repository.list_strategy_versions()
    references = {}
    for number in (9, 10, 12):
        version = next(item for item in versions if item.strategy_family == "sma"
                       and item.symbol == "BTC/USDT" and item.timeframe == "4h" and item.version_number == number)
        references[number] = repository.list_runs_for_strategy(version.strategy_key, limit=None)[0]
    template = replace(config_for_run(references[10]), trend_entry_buffer=0,
                       exit_mode="signal", trailing_activation=None, trailing_distance=None,
                       trailing_reentry_mode="inherit")
    rows = []
    for year, end in ((2023, "2024-01-01"), (2024, "2025-01-01"),
                      (2025, "2026-01-01"), (2026, "2026-10-20")):
        start_ms = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp()*1000)
        end_ms = int(datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp()*1000)
        history = CandleRepository(args.db).list_range("binance", "BTC/USDT", "4h", start_ms-180*TIMEFRAMES_MS["4h"], end_ms)
        expected = list(range(start_ms-180*TIMEFRAMES_MS["4h"], end_ms, TIMEFRAMES_MS["4h"]))
        if [c.timestamp_ms for c in history] != expected:
            raise ValueError(f"incomplete source data for {year}")
        variants = {}
        for number, run in references.items():
            config = config_for_run(run)
            variants[f"V{number}"] = (config, strategy_for_run(run, config))
        variants.update({
            "donchian_midpoint_20d": (template, DonchianMidpoint()),
            "bollinger_20_2_atr14_2": (template, BollingerAtr()),
            "sma_v12_atr14_2": (config_for_run(references[12]), AtrProtection(strategy_for_run(references[12], config_for_run(references[12])))),
        })
        for name, (config, strategy) in variants.items():
            for cost_multiplier in (1, 2):
                cfg = replace(config, fee_bps=config.fee_bps*cost_multiplier,
                              slippage_bps=config.slippage_bps*cost_multiplier)
                # Stateful strategies must be fresh for each independent cost run.
                if name == "donchian_midpoint_20d": strategy = DonchianMidpoint()
                recorded = RecordedSignals(strategy)
                result = BacktestEngine(cfg).run(history, recorded, evaluation_start_ms=start_ms)
                row = dict(year=year, until_exclusive=end, strategy=name, cost_multiplier=cost_multiplier,
                           data_fingerprint=_fingerprint(history), config=asdict(cfg),
                           result=json.loads(serialize_result(result)),
                           leverage_audit=leverage_audit(result, cfg, recorded))
                rows.append(row)
                print(year, name, "cost", cost_multiplier, "return", round(result.metrics.total_return*100,3),
                      "DD", round(result.metrics.maximum_drawdown*100,3), "trades", len(result.trades), flush=True)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(dict(target=0.15, risk_fraction=0.005,
                    design="Three fixed exploratory hypotheses, no parameter sweep or version saves. 2024/2025 are development; 2023 and 2026 controls already viewed, not unseen. No validated leveraged PnL.",
                    rows=rows), allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
