from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class MarginBracket:
    notional_floor: float
    notional_cap: float
    maintenance_margin_rate: float
    cumulative_maintenance_amount: float = 0.0

    def __post_init__(self) -> None:
        values = (
            self.notional_floor,
            self.notional_cap,
            self.maintenance_margin_rate,
            self.cumulative_maintenance_amount,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("margin bracket values must be finite")
        if self.notional_floor < 0 or self.notional_cap <= self.notional_floor:
            raise ValueError("invalid margin bracket range")
        if not 0 < self.maintenance_margin_rate < 1:
            raise ValueError("maintenance margin rate must be in (0, 1)")
        if self.cumulative_maintenance_amount < 0:
            raise ValueError("cumulative maintenance amount cannot be negative")


class MaintenanceMarginModel:
    """Binance-style notional brackets used for isolated margin checks."""

    def __init__(self, brackets: list[MarginBracket]) -> None:
        if not brackets:
            raise ValueError("at least one margin bracket is required")
        self.brackets = sorted(brackets, key=lambda item: item.notional_floor)
        for previous, current in zip(self.brackets, self.brackets[1:]):
            if previous.notional_cap != current.notional_floor:
                raise ValueError("margin brackets must be contiguous")

    def bracket_for(self, notional: float) -> MarginBracket:
        if not isfinite(notional) or notional < 0:
            raise ValueError("notional must be finite and non-negative")
        for bracket in self.brackets:
            if bracket.notional_floor <= notional < bracket.notional_cap:
                return bracket
        if notional == self.brackets[-1].notional_cap:
            return self.brackets[-1]
        raise ValueError("position notional exceeds the margin bracket snapshot")

    def maintenance_margin(self, quantity: float, mark_price: float) -> float:
        notional = abs(quantity) * mark_price
        bracket = self.bracket_for(notional)
        return max(
            0.0,
            notional * bracket.maintenance_margin_rate
            - bracket.cumulative_maintenance_amount,
        )

    def margin_ratio(
        self, quantity: float, mark_price: float, margin_balance: float
    ) -> float:
        if margin_balance <= 0:
            return float("inf")
        return self.maintenance_margin(quantity, mark_price) / margin_balance

    def is_liquidated(
        self, quantity: float, mark_price: float, margin_balance: float
    ) -> bool:
        return margin_balance <= self.maintenance_margin(quantity, mark_price)

    def liquidation_price_long(
        self,
        quantity: float,
        entry_price: float,
        isolated_margin: float,
        funding: float = 0.0,
    ) -> float:
        if quantity <= 0 or entry_price <= 0 or isolated_margin <= 0:
            raise ValueError("long liquidation inputs must be positive")

        def excess_margin(price: float) -> float:
            balance = isolated_margin + quantity * (price - entry_price) + funding
            return balance - self.maintenance_margin(quantity, price)

        low = max(entry_price * 1e-9, 1e-12)
        high = entry_price
        if excess_margin(low) > 0:
            return 0.0
        if excess_margin(high) <= 0:
            return high
        for _ in range(80):
            middle = (low + high) / 2
            if excess_margin(middle) <= 0:
                low = middle
            else:
                high = middle
        return high
