from pathlib import Path

from app.strategies.sweep_context_exit import DirectionalSweepContextExitStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False,intraday_exit_candidate=DirectionalSweepContextExitStrategy(),
        parent_path=Path("data/perpetual-directional-loss-guard.json"),parent_variant="portfolio_directional_loss_guard",
        variant="portfolio_sweep_context_exit",output=Path("data/perpetual-sweep-context-exit.json"))
