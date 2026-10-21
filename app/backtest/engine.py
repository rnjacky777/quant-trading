from dataclasses import dataclass
from math import isfinite

from app.backtest.fees import fee_amount
from app.backtest.metrics import calculate_metrics
from app.backtest.models import BacktestConfig, BacktestResult, EquityPoint, Trade
from app.backtest.slippage import execution_price
from app.data.models import Candle, FundingRate, MarkPriceCandle, TIMEFRAMES_MS
from app.risk.margin import MaintenanceMarginModel
from app.strategies.base import Action, Strategy


@dataclass
class _OpenPosition:
    entry_timestamp_ms: int
    entry_price: float
    quantity: float
    entry_notional: float
    entry_fee: float
    entry_slippage: float
    margin: float
    stop_loss_price: float | None
    take_profit_price: float | None
    funding: float = 0.0


class BacktestEngine:
    """Long/cash baseline engine with next-bar execution and explicit costs."""

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()

    def run(
        self,
        candles: list[Candle],
        strategy: Strategy,
        *,
        evaluation_start_ms: int | None = None,
        funding_rates: list[FundingRate] | None = None,
        mark_prices: list[MarkPriceCandle] | None = None,
        margin_model: MaintenanceMarginModel | None = None,
    ) -> BacktestResult:
        self._validate_candles(candles)
        self._validate_derivatives_inputs(funding_rates, mark_prices, margin_model)
        cash = self.config.initial_cash
        position: _OpenPosition | None = None
        trades: list[Trade] = []
        maximum_margin_ratio = 0.0
        funding_rates = funding_rates or []
        mark_prices = mark_prices or []
        interval = TIMEFRAMES_MS[candles[0].timeframe]
        start_index = self._evaluation_start_index(candles, evaluation_start_ms)
        curve = [
            EquityPoint(candles[start_index].timestamp_ms - interval, cash, False)
        ]

        for index in range(start_index, len(candles)):
            signal = strategy.generate(candles[:index])
            candle = candles[index]
            if signal.symbol != candle.symbol:
                raise ValueError("strategy returned a signal for another symbol")
            signal_timestamp_ms = int(signal.timestamp.timestamp() * 1000)
            if signal_timestamp_ms != candles[index - 1].timestamp_ms:
                raise ValueError("strategy signal timestamp must match the completed candle")
            if signal.action is Action.SELL and position is not None:
                cash, trade = self._sell(
                    cash, position, candle, candle.open, exit_reason="signal"
                )
                trades.append(trade)
                position = None
            elif signal.action is Action.BUY and position is None:
                cash, position = self._buy(cash, candle)

            if position is not None:
                bar_end = candle.timestamp_ms + interval
                bar_marks = [
                    mark for mark in mark_prices
                    if candle.timestamp_ms <= mark.timestamp_ms < bar_end
                ]
                if margin_model is not None:
                    if not bar_marks:
                        raise ValueError("perpetual backtest has a missing mark-price interval")
                    bar_funding = [
                        funding for funding in funding_rates
                        if candle.timestamp_ms <= funding.timestamp_ms < bar_end
                    ]
                    funding_index = 0
                    for mark in bar_marks:
                        while (
                            funding_index < len(bar_funding)
                            and bar_funding[funding_index].timestamp_ms <= mark.timestamp_ms
                        ):
                            cash += self._apply_funding(
                                position, bar_funding[funding_index]
                            )
                            funding_index += 1
                        margin_balance = self._margin_balance(position, mark.low)
                        ratio = margin_model.margin_ratio(
                            position.quantity, mark.low, margin_balance
                        )
                        maximum_margin_ratio = max(
                            maximum_margin_ratio, ratio if isfinite(ratio) else 1.0
                        )
                        if margin_model.is_liquidated(
                            position.quantity, mark.low, margin_balance
                        ):
                            liquidation_price = margin_model.liquidation_price_long(
                                position.quantity,
                                position.entry_price,
                                position.margin,
                                position.funding,
                            )
                            reference_price = min(mark.open, liquidation_price)
                            cash, trade = self._sell(
                                cash,
                                position,
                                candle,
                                reference_price,
                                exit_reason="liquidation",
                            )
                            trades.append(trade)
                            position = None
                            break
                    while position is not None and funding_index < len(bar_funding):
                        cash += self._apply_funding(position, bar_funding[funding_index])
                        funding_index += 1

            if position is not None:
                risk_exit = self._risk_exit(position, candle)
                if risk_exit is not None:
                    reference_price, exit_reason = risk_exit
                    cash, trade = self._sell(
                        cash, position, candle, reference_price, exit_reason=exit_reason
                    )
                    trades.append(trade)
                    position = None

            if (
                self.config.market_type == "spot"
                and position is not None
                and self._position_equity(cash, position, candle.close) <= 0
            ):
                cash, trade = self._sell(
                    cash, position, candle, candle.close, exit_reason="liquidation"
                )
                trades.append(trade)
                position = None
            equity = (
                self._position_equity(cash, position, candle.close)
                if position else cash
            )
            curve.append(EquityPoint(candle.timestamp_ms, equity, position is not None))

        if position is not None:
            final_candle = candles[-1]
            cash, trade = self._sell(
                cash, position, final_candle, final_candle.close, exit_reason="end_of_data"
            )
            trades.append(trade)
            curve[-1] = EquityPoint(final_candle.timestamp_ms, cash, False)

        metrics = calculate_metrics(
            curve,
            trades,
            self.config.initial_cash,
            candles[0].timeframe,
            maximum_margin_ratio,
        )
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

    @staticmethod
    def _evaluation_start_index(
        candles: list[Candle], evaluation_start_ms: int | None
    ) -> int:
        if evaluation_start_ms is None:
            return 1
        if not candles[0].timestamp_ms <= evaluation_start_ms <= candles[-1].timestamp_ms:
            raise ValueError("evaluation start must fall inside candle data")
        index = next(
            (
                index
                for index, candle in enumerate(candles)
                if candle.timestamp_ms >= evaluation_start_ms
            ),
            len(candles),
        )
        return max(1, index)

    def _buy(self, cash: float, candle: Candle) -> tuple[float, _OpenPosition]:
        price = execution_price(candle.open, self.config.slippage_bps, is_buy=True)
        available = cash * self.config.position_fraction
        fee_rate = self.config.fee_bps / 10_000
        margin = available / (1 + self.config.leverage * fee_rate)
        notional = margin * self.config.leverage
        fee = fee_amount(notional, self.config.fee_bps)
        quantity = notional / price
        slippage = quantity * (price - candle.open)
        return cash - notional - fee, _OpenPosition(
            candle.timestamp_ms,
            price,
            quantity,
            notional,
            fee,
            slippage,
            margin,
            price * (1 - self.config.stop_loss_pct)
            if self.config.stop_loss_pct else None,
            price * (1 + self.config.take_profit_pct)
            if self.config.take_profit_pct else None,
        )

    def _sell(
        self,
        cash: float,
        position: _OpenPosition,
        candle: Candle,
        reference_price: float,
        exit_reason: str,
    ) -> tuple[float, Trade]:
        price = execution_price(reference_price, self.config.slippage_bps, is_buy=False)
        proceeds = position.quantity * price
        exit_fee = fee_amount(proceeds, self.config.fee_bps)
        exit_slippage = position.quantity * (reference_price - price)
        liquidation_fee = (
            fee_amount(proceeds, self.config.liquidation_fee_bps)
            if exit_reason == "liquidation" else 0.0
        )
        price_pnl = proceeds - position.entry_notional
        pnl = (
            price_pnl + position.funding - exit_fee - position.entry_fee
            - liquidation_fee
        )
        invested = position.margin + position.entry_fee
        return cash + position.entry_notional + price_pnl - exit_fee - liquidation_fee, Trade(
            entry_timestamp_ms=position.entry_timestamp_ms,
            exit_timestamp_ms=candle.timestamp_ms,
            entry_price=position.entry_price,
            exit_price=price,
            quantity=position.quantity,
            pnl=pnl,
            return_pct=pnl / invested,
            fees=position.entry_fee + exit_fee,
            slippage_cost=position.entry_slippage + exit_slippage,
            exit_reason=exit_reason,
            stop_loss_price=position.stop_loss_price,
            take_profit_price=position.take_profit_price,
            leverage=self.config.leverage,
            funding=position.funding,
            liquidation_fee=liquidation_fee,
        )

    @staticmethod
    def _apply_funding(position: _OpenPosition, funding: FundingRate) -> float:
        cashflow = -(position.quantity * funding.mark_price * funding.rate)
        position.funding += cashflow
        return cashflow

    @staticmethod
    def _margin_balance(position: _OpenPosition, mark_price: float) -> float:
        return (
            position.margin
            + position.quantity * (mark_price - position.entry_price)
            + position.funding
        )

    @staticmethod
    def _position_equity(cash: float, position: _OpenPosition, price: float) -> float:
        return cash + position.entry_notional + position.quantity * (
            price - position.entry_price
        )

    @staticmethod
    def _risk_exit(
        position: _OpenPosition, candle: Candle
    ) -> tuple[float, str] | None:
        if position.stop_loss_price is not None and candle.low <= position.stop_loss_price:
            return min(candle.open, position.stop_loss_price), "stop_loss"
        if position.take_profit_price is not None and candle.high >= position.take_profit_price:
            return max(candle.open, position.take_profit_price), "take_profit"
        return None

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

    def _validate_derivatives_inputs(
        self,
        funding_rates: list[FundingRate] | None,
        mark_prices: list[MarkPriceCandle] | None,
        margin_model: MaintenanceMarginModel | None,
    ) -> None:
        supplied = (funding_rates is not None, mark_prices is not None, margin_model is not None)
        if self.config.market_type == "perpetual" and not all(supplied):
            raise ValueError(
                "perpetual backtest requires funding rates, mark prices, and margin brackets"
            )
        if self.config.market_type == "spot" and any(supplied):
            raise ValueError("derivatives data can only be used in perpetual mode")
