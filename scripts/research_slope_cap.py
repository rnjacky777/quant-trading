from pathlib import Path

from scripts.research_portfolio_overlap import run_experiment


if __name__=='__main__':
    run_experiment(risk_decay=False,slope_risk_cap=True,
        parent_path=Path('data/perpetual-swing-failure-exit.json'),parent_variant='portfolio_swing_failure_exit',
        variant='portfolio_slope_risk_cap',output=Path('data/perpetual-slope-risk-cap.json'))
