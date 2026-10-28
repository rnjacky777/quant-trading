from pathlib import Path

from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False,swing_price_protection=True,
        parent_path=Path("data/perpetual-confirmed-efficiency.json"),parent_variant="portfolio_confirmed_efficiency",
        variant="portfolio_swing_protection",output=Path("data/perpetual-swing-protection.json"))
