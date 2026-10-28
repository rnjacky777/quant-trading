import pytest

from scripts.research_btc_leverage import risk_sizing


def test_leverage_is_minimum_required_and_cost_inclusive_risk_is_preserved():
    for risk in (.005, .02, .05, .10):
        sizing = risk_sizing(risk, .05, 10, 5)
        exposure = sizing["target_effective_exposure"]
        leverage = sizing["exchange_leverage"]
        assert leverage - 1 < exposure <= leverage
        actual_exposure = sizing["position_fraction"] * leverage / (1 + leverage * .001)
        assert actual_exposure == pytest.approx(exposure)
        assert exposure * (sizing["price_and_fee_risk_fraction"] + .001) == pytest.approx(risk)


def test_risk_scenario_above_registered_leverage_limit_is_rejected():
    with pytest.raises(ValueError, match="limits"):
        risk_sizing(.20, .05, 10, 5)
