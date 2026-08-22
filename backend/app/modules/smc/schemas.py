from __future__ import annotations

from pydantic import BaseModel


class SwingPoint(BaseModel):
    time: str
    value: float


class MSSignal(BaseModel):
    time: str
    price: float
    label: str  # BOS / CHoCH / CHoCH+
    bull: bool


class SmcBox(BaseModel):
    """Order block or FVG rendered as a horizontal zone."""

    time: str  # bar where the zone starts
    top: float
    btm: float
    mitigated: bool


class FVGBox(BaseModel):
    time: str
    bull: bool
    top: float
    btm: float
    mitigated: bool


class SmcResponse(BaseModel):
    symbol: str
    interval: str
    period: str
    swing_highs: list[SwingPoint]
    swing_lows: list[SwingPoint]
    ms_signals: list[MSSignal]
    bull_obs: list[SmcBox]
    bear_obs: list[SmcBox]
    fvgs: list[FVGBox]
    range_high: float | None = None
    range_low: float | None = None
    equilibrium: float | None = None
    itrend: int
    strend: int
