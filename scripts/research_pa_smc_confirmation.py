"""One entry-category experiment; no fast-exit or risk-decay stacking."""
from pathlib import Path

from app.strategies.swing_confirmation import DirectionalSwingConfirmationStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False,
        swing_entry_candidate=DirectionalSwingConfirmationStrategy(),
        parent_path=Path("data/perpetual-pa-smc.json"), parent_variant="portfolio_pa_smc",
        variant="portfolio_pa_smc_confirmation",
        output=Path("data/perpetual-pa-smc-confirmation.json"))
