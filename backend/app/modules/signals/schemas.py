from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


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


# ── Fusion schemas ──────────────────────────────────────────────────────────


class LayerDetail(BaseModel):
    score: float
    label: str
    weight: float


class TechnicalLayer(LayerDetail):
    signals: list[dict[str, str]] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class MlLayer(LayerDetail):
    available: bool = False
    up_prob: float = 50.0
    confidence: float = 50.0
    horizon: dict[str, Any] = Field(default_factory=dict)
    model_accs: dict[str, float] = Field(default_factory=dict)
    conf_tier: dict[str, str] = Field(default_factory=dict)
    walk_fwd_acc: float = 0.0
    active_models: str = ""


class NewsLayer(LayerDetail):
    available: bool = False
    detail: list[dict[str, Any]] = Field(default_factory=list)


class FusionLayers(BaseModel):
    technical: TechnicalLayer
    ml: MlLayer
    news: NewsLayer


class FusionResponse(BaseModel):
    symbol: str
    fused_score: float = Field(ge=-1.0, le=1.0)
    final_label: str
    final_desc: str
    confidence_tier: str
    confidence_tone: str
    missing: list[str] = Field(default_factory=list)
    layers: FusionLayers
