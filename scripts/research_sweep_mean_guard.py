from pathlib import Path

from app.strategies.sweep_mean_guard import DirectionalSweepMeanGuardStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False,entry_candidate=DirectionalSweepMeanGuardStrategy(),
        parent_path=Path("data/perpetual-confirmed-efficiency.json"),parent_variant="portfolio_confirmed_efficiency",
        variant="portfolio_sweep_mean_guard",output=Path("data/perpetual-sweep-mean-guard.json"))
