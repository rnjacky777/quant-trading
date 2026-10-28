from pathlib import Path

from app.strategies.swing_volume import DirectionalSwingVolumeStrategy
from scripts.research_portfolio_overlap import run_experiment


if __name__=='__main__':
    run_experiment(risk_decay=False,swing_entry_candidate=DirectionalSwingVolumeStrategy(),
        parent_path=Path('data/perpetual-swing-failure-exit.json'),parent_variant='portfolio_swing_failure_exit',
        variant='portfolio_swing_volume',output=Path('data/perpetual-swing-volume.json'))
