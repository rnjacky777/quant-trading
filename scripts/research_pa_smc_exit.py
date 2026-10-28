"""One preregistered exit-category experiment on the PA/SMC parent."""
from pathlib import Path

from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False, swing_exit_lookback=5,
        parent_path=Path("data/perpetual-pa-smc.json"), parent_variant="portfolio_pa_smc",
        variant="portfolio_pa_smc_fast_exit", output=Path("data/perpetual-pa-smc-exit.json"))
