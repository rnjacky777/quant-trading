from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.strategies.base import Action
from app.strategies.directional_intraday import DirectionalSignal
from tests.test_portfolio_research import Side, config, run, tape


class ExitingSide(Side):
    """Enter once, then request a strategy exit on every later bar."""

    def generate(self, candles):
        signal = super().generate(candles)
        if len(candles) == 1:
            return signal
        return DirectionalSignal("BTC/USDT", datetime.fromtimestamp(candles[-1].timestamp_ms / 1000, timezone.utc),
                                 Action.HOLD, 0, self.name, direction=0, exit_long=True, exit_short=True)


def engine(sleeve, direction, hold=True):
    return PortfolioResearchEngine([ResearchSleeve(sleeve, ExitingSide(direction), config(holding_hours=168))],
                                   swing_long_signal_hold=hold)


def test_swing_long_ignores_signal_exit_until_72h():
    held = run(engine("swing", 1), tape(80)).trades[0]
    assert held.exit_reason == "signal"
    assert held.exit_timestamp_ms - held.entry_timestamp_ms == 72 * 3600000
    assert run(engine("swing", 1, hold=False), tape(80)).trades[0].exit_timestamp_ms == 2 * 3600000


@pytest.mark.parametrize("sleeve,direction", [("swing", -1), ("intraday", 1), ("intraday", -1)])
def test_other_sleeves_and_short_side_are_unchanged(sleeve, direction):
    trade = run(engine(sleeve, direction), tape(80)).trades[0]
    assert trade.exit_reason == "signal" and trade.exit_timestamp_ms == 2 * 3600000


def test_stop_still_applies_during_hold():
    bars = tape(80)
    bars[10] = replace(bars[10], open=79, low=79)
    trade = run(engine("swing", 1), bars).trades[0]
    assert trade.exit_reason == "stop_loss" and trade.exit_timestamp_ms == 10 * 3600000


def test_flag_must_be_boolean():
    with pytest.raises(ValueError):
        PortfolioResearchEngine([ResearchSleeve("swing", Side(1), config())], swing_long_signal_hold=1)
