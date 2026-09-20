from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    db_path: Path
    exchange_id: str
    live_trading: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            db_path=Path(os.getenv("QUANT_DB_PATH", "data/market.sqlite3")),
            exchange_id=os.getenv("QUANT_EXCHANGE", "binance"),
            live_trading=os.getenv("LIVE_TRADING", "false").lower() == "true",
        )
