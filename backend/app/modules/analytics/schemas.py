from __future__ import annotations

from pydantic import BaseModel


class SeriesPoint(BaseModel):
    time: str
    value: float


class IndicatorsResponse(BaseModel):
    symbol: str
    interval: str
    period: str
    sma20: list[SeriesPoint] = []
    sma50: list[SeriesPoint] = []
    ema20: list[SeriesPoint] = []
    bb_high: list[SeriesPoint] = []
    bb_mid: list[SeriesPoint] = []
    bb_low: list[SeriesPoint] = []
    rsi: list[SeriesPoint] = []
    atr: list[SeriesPoint] = []
    macd: list[SeriesPoint] = []
    macd_signal: list[SeriesPoint] = []
    macd_hist: list[SeriesPoint] = []


class SupportResistanceResponse(BaseModel):
    supports: list[float]
    resistances: list[float]
    nearest_support: float | None = None
    nearest_resistance: float | None = None
