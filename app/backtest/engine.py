from dataclasses import dataclass

from app.backtest.fees import fee_amount
from app.backtest.metrics import calculate_metrics
from app.backtest.models import BacktestConfig, BacktestResult, EquityPoint, Trade
from app.backtest.slippage import execution_price
from app.data.models import Candle, TIMEFRAMES_MS
from app.strategies.base import Action, Strategy


@dataclass
class _OpenPosition:
    entry_timestamp_ms: int
    entry_price: float
    quantity: float
    entry_notional: float
    entry_fee: float
    entry_slippage: float


class BacktestEngine:
    """Long/cash baseline engine with next-bar execution and explicit costs."""

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()

    def run(self, candles: list[Candle], strategy: Strategy) -> BacktestResult:
        self._validate_candles(candles)
        cash = self.config.initial_cash
        position: _OpenPosition | None = None
        trades: list[Trade] = []
        curve = [EquityPoint(candles[0].timestamp_ms, cash, False)]

        for index in range(1, len(candles)):
            signal = strategy.generate(candles[:index])
            candle = candles[index]
            if signal.symbol != candle.symbol:
                raise ValueError("strategy returned a signal for another symbol")
            signal_timestamp_ms = int(signal.timestamp.timestamp() * 1000)
            if signal_timestamp_ms != candles[index - 1].timestamp_ms:
                raise ValueError("strategy signal timestamp must match the completed candle")
            if signal.action is Action.BUY and position is None:
                cash, position = self._buy(cash, candle)
            elif signal.action is Action.SELL and position is not None:
                cash, trade = self._sell(cash, position, candle, candle.open)
                trades.append(trade)
                position = None
            equity = cash + (position.quantity * candle.close if position else 0.0)
            curve.append(EquityPoint(candle.timestamp_ms, equity, position is not None))

        if position is not None:
            final_candle = candles[-1]
            cash, trade = self._sell(cash, position, final_candle, final_candle.close)
            trades.append(trade)
            curve[-1] = EquityPoint(final_candle.timestamp_ms, cash, False)

        metrics = calculate_metrics(curve, trades, self.config.initial_cash, candles[0].timeframe)
        return BacktestResult(
            strategy_name=strategy.name,
            symbol=candles[0].symbol,
            timeframe=candles[0].timeframe,
            initial_cash=self.config.initial_cash,
            final_equity=curve[-1].equity,
            metrics=metrics,
            trades=trades,
            equity_curve=curve,
        )

    def _buy(self, cash: float, candle: Candle) -> tuple[float, _OpenPosition]:
        price = execution_price(candle.open, self.config.slippage_bps, is_buy=True)
        available = cash * self.config.position_fraction
        notional = available / (1 + self.config.fee_bps / 10_000)
        fee = fee_amount(notional, self.config.fee_bps)
        quantity = notional / price
        slippage = quantity * (price - candle.open)
        return cash - notional - fee, _OpenPosition(
            candle.timestamp_ms, price, quantity, notional, fee, slippage
        )

    def _sell(
        self,
        cash: float,
        position: _OpenPosition,
        candle: Candle,
        reference_price: float,
    ) -> tuple[float, Trade]:
        price = execution_price(reference_price, self.config.slippage_bps, is_buy=False)
        proceeds = position.quantity * price
        exit_fee = fee_amount(proceeds, self.config.fee_bps)
        exit_slippage = position.quantity * (reference_price - price)
        pnl = proceeds - exit_fee - position.entry_notional - position.entry_fee
        invested = position.entry_notional + position.entry_fee
        return cash + proceeds - exit_fee, Trade(
            entry_timestamp_ms=position.entry_timestamp_ms,
            exit_timestamp_ms=candle.timestamp_ms,
            entry_price=position.entry_price,
            exit_price=price,
            quantity=position.quantity,
            pnl=pnl,
            return_pct=pnl / invested,
            fees=position.entry_fee + exit_fee,
            slippage_cost=position.entry_slippage + exit_slippage,
        )

    @staticmethod
    def _validate_candles(candles: list[Candle]) -> None:
        if len(candles) < 2:
            raise ValueError("backtest needs at least two candles")
        first = candles[0]
        interval = TIMEFRAMES_MS[first.timeframe]
        for previous, current in zip(candles, candles[1:]):
            if (current.exchange, current.symbol, current.timeframe) != (
                first.exchange, first.symbol, first.timeframe
            ):
                raise ValueError("candles must share exchange, symbol, and timeframe")
            if current.timestamp_ms - previous.timestamp_ms != interval:
                raise ValueError("candles contain a duplicate, disorder, or missing interval")
