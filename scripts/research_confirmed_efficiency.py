"""Run exactly one signal change on every delayed-confirmation experiment."""
from pathlib import Path

from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False, swing_entry_candidate=DirectionalSwingEfficiencyStrategy(),
        parent_path=Path("data/perpetual-pa-smc-confirmation.json"),
        parent_variant="portfolio_pa_smc_confirmation", variant="portfolio_confirmed_efficiency",
        output=Path("data/perpetual-confirmed-efficiency.json"))
