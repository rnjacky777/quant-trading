from pathlib import Path

from app.strategies.sweep_no_atr_floor import DirectionalSweepNoAtrFloorStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__=='__main__':
    run_experiment(risk_decay=False,entry_candidate=DirectionalSweepNoAtrFloorStrategy(),
        parent_path=Path('data/perpetual-swing-failure-exit.json'),parent_variant='portfolio_swing_failure_exit',
        variant='portfolio_sweep_no_atr_floor',output=Path('data/perpetual-atr-ablation.json'))
