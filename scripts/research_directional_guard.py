from pathlib import Path

from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False,directional_loss_guard=True,
        parent_path=Path("data/perpetual-sweep-structural-stop.json"),parent_variant="portfolio_sweep_structural_stop",
        variant="portfolio_directional_loss_guard",output=Path("data/perpetual-directional-loss-guard.json"))
