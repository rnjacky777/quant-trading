from pathlib import Path

from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False,entry_candidate=DirectionalSweepStructureConfirmStrategy(),
        parent_path=Path("data/perpetual-directional-loss-guard.json"),parent_variant="portfolio_directional_loss_guard",
        variant="portfolio_sweep_structure_confirm",output=Path("data/perpetual-sweep-structure-confirm.json"))
