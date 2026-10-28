from dataclasses import asdict
import json
from math import isfinite
from typing import Any

from app.backtest.models import BacktestResult, EquityPoint, PerformanceMetrics, Trade


def _encode(value: Any) -> Any:
    if isinstance(value, float) and not isfinite(value):
        return {"__float__": str(value)}
    if isinstance(value, dict):
        return {key: _encode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_encode(item) for item in value]
    return value


def _decode(value: dict[str, Any]) -> Any:
    return float(value["__float__"]) if set(value) == {"__float__"} else value


def serialize_result(result: BacktestResult) -> str:
    return json.dumps(_encode(asdict(result)), sort_keys=True, separators=(",", ":"), allow_nan=False)


def deserialize_result(payload: str) -> BacktestResult:
    values = json.loads(payload, object_hook=_decode)
    values["metrics"] = PerformanceMetrics(**values["metrics"])
    values["trades"] = [Trade(**trade) for trade in values["trades"]]
    values["equity_curve"] = [EquityPoint(**point) for point in values["equity_curve"]]
    return BacktestResult(**values)
