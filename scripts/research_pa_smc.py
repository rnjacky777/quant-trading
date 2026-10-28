from pathlib import Path

from app.strategies.pa_smc import DirectionalSweepStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__=="__main__":
    run_experiment(entry_candidate=DirectionalSweepStrategy(),risk_decay=False,
        variant="portfolio_pa_smc",output=Path("data/perpetual-pa-smc.json"))
