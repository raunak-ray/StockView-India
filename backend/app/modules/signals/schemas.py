from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class RuleOut(BaseModel):
    rule: str
    kind: Literal["buy", "sell", "neut"]


class MarkerOut(BaseModel):
    time: str
    position: Literal["aboveBar", "belowBar"]
    kind: Literal["buy", "sell"]
    price: float


class SignalResponse(BaseModel):
    symbol: str
    verdict: str
    score: int
    confidence: float
    rules: list[RuleOut]
    reasons: list[str]
    markers: list[MarkerOut]
