from pathlib import Path

from app.strategies.directional_pullback import DirectionalPullbackStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__=="__main__":
    run_experiment(risk_decay=False,entry_candidate=DirectionalPullbackStrategy(),
        parent_path=Path("data/perpetual-confirmed-efficiency.json"),parent_variant="portfolio_confirmed_efficiency",
        variant="portfolio_directional_pullback",output=Path("data/perpetual-directional-pullback.json"))
