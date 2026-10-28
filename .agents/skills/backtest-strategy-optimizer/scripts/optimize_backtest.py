"""Delegate to the versioned project implementation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from scripts.optimize_backtest import main

if __name__ == "__main__":
    main()
