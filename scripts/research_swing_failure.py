from pathlib import Path

from scripts.research_portfolio_overlap import run_experiment


if __name__ == "__main__":
    run_experiment(risk_decay=False,swing_failure_exit=True,
        parent_path=Path('data/perpetual-sweep-structure-confirm.json'),
        parent_variant='portfolio_sweep_structure_confirm',variant='portfolio_swing_failure_exit',
        output=Path('data/perpetual-swing-failure-exit.json'))
