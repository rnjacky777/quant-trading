from pathlib import Path

from scripts.research_portfolio_overlap import run_experiment


if __name__ == '__main__':
    run_experiment(risk_decay=False, swing_short_risk_cap=True,
        parent_path=Path('data/perpetual-swing-failure-exit.json'),
        parent_variant='portfolio_swing_failure_exit',
        variant='portfolio_swing_short_risk_cap',
        output=Path('data/perpetual-swing-short-risk-cap.json'))
