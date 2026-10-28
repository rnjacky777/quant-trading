from pathlib import Path

from app.strategies.sweep_structural_stop import DirectionalSweepStructuralStopStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False,intraday_exit_candidate=DirectionalSweepStructuralStopStrategy(),
        parent_path=Path("data/perpetual-confirmed-efficiency.json"),parent_variant="portfolio_confirmed_efficiency",
        variant="portfolio_sweep_structural_stop",output=Path("data/perpetual-sweep-structural-stop.json"))
