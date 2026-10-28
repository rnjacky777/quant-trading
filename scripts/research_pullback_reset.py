from pathlib import Path

from app.strategies.pullback_reset import DirectionalPullbackResetStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False, entry_candidate=DirectionalPullbackResetStrategy(),
        parent_path=Path("data/perpetual-directional-pullback.json"), parent_variant="portfolio_directional_pullback",
        variant="portfolio_pullback_reset", output=Path("data/perpetual-pullback-reset.json"))
