from pathlib import Path

from app.strategies.sweep_window import DirectionalSweepWindowStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False, entry_candidate=DirectionalSweepWindowStrategy(),
        parent_path=Path("data/perpetual-confirmed-efficiency.json"),
        parent_variant="portfolio_confirmed_efficiency", variant="portfolio_sweep_window",
        output=Path("data/perpetual-sweep-frequency.json"))
