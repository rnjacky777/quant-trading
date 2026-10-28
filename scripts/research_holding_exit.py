"""One exit change, no new entries or reduced execution cost assumptions."""
from pathlib import Path

from scripts.research_portfolio_overlap import run_experiment


if __name__=="__main__":
    run_experiment(risk_decay=False,intraday_holding_hours=48,
        parent_path=Path("data/perpetual-confirmed-efficiency.json"),parent_variant="portfolio_confirmed_efficiency",
        variant="portfolio_holding_48h",output=Path("data/perpetual-holding-exit.json"))
