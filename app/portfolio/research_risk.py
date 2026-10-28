"""Shared gross exposure, stop-risk and collateral admission for research lots."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class PortfolioLimits:
    max_gross_exposure: float = .5
    max_open_stop_risk: float = .01
    max_margin_fraction: float = .5
    daily_entries: int = 2
    same_direction_risk_decay: bool = False

    def __post_init__(self) -> None:
        if type(self.same_direction_risk_decay) is not bool:
            raise ValueError("same-direction risk decay must be boolean")
        values=(self.max_gross_exposure,self.max_open_stop_risk,self.max_margin_fraction)
        if not all(isfinite(x) and 0<x<=1 for x in values):
            raise ValueError("portfolio limits must be finite fractions in(0,1]")
        if type(self.daily_entries) is not int or self.daily_entries<1:
            raise ValueError("daily portfolio entry limit must be positive")


@dataclass(frozen=True)
class RiskLot:
    quantity: float
    direction: int
    stop: float
    margin: float
    fee_bps: float
    slippage_bps: float
    funding_reserve: float


@dataclass(frozen=True)
class PortfolioUsage:
    gross: float = 0
    net: float = 0
    margin: float = 0
    open_stop_risk: float = 0


def portfolio_usage(lots: list[RiskLot], mark: float) -> PortfolioUsage:
    gross=net=margin=risk=0.0
    for lot in lots:
        value=lot.quantity*mark
        gross+=value
        net+=lot.direction*value
        margin+=lot.margin
        stop_fill=lot.stop*(1-lot.direction*lot.slippage_bps/10000)
        future_loss=max(0,lot.direction*(mark-stop_fill))
        risk+=lot.quantity*(future_loss+stop_fill*lot.fee_bps/10000+mark*lot.funding_reserve)
    return PortfolioUsage(gross,net,margin,risk)


def admission_fraction(*, equity: float, cash: float, usage: PortfolioUsage,
        notional: float, margin_and_fee: float, planned_risk: float, limits: PortfolioLimits) -> tuple[float,str]:
    if equity<=0 or min(notional,margin_and_fee,planned_risk)<=0:
        return 0,"invalid_budget"
    available_margin=min(cash-usage.margin,equity*limits.max_margin_fraction-usage.margin)
    fractions={"gross_exposure":(equity*limits.max_gross_exposure-usage.gross)/notional,
        "open_stop_risk":(equity*limits.max_open_stop_risk-usage.open_stop_risk)/planned_risk,
        "available_collateral":available_margin/margin_and_fee}
    binding=min(fractions,key=fractions.get)
    fraction=max(0,min(1,fractions[binding]))
    return fraction,"full_budget" if fraction==1 else binding
