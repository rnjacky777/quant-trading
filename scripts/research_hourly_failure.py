from pathlib import Path

from scripts.research_portfolio_overlap import run_experiment


if __name__ == '__main__':
    run_experiment(risk_decay=False, swing_hourly_failure=True,
        parent_path=Path('data/perpetual-swing-failure-exit.json'),
        parent_variant='portfolio_swing_failure_exit',
        variant='portfolio_swing_hourly_failure',
        output=Path('data/perpetual-swing-hourly-failure.json'))
