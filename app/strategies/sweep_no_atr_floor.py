"""Ablate the inherited hourly ATR floor, retaining the full sweep structure."""
from app.strategies.sweep_structure_confirm import DirectionalSweepStructureConfirmStrategy


class DirectionalSweepNoAtrFloorStrategy(DirectionalSweepStructureConfirmStrategy):
    name = 'perpetual_sweep_structure_without_hourly_atr_floor'
    minimum_atr_fraction = 0.
