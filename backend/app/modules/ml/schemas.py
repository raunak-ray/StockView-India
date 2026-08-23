from typing import Any

from pydantic import BaseModel, Field


class CapabilitiesResponse(BaseModel):
    sklearn: bool
    xgboost: bool
    lightgbm: bool
    catboost: bool
    torch: bool
    shap: bool
    active_ensemble: list[str] = Field(description="Models that will vote")


class JobCreatedResponse(BaseModel):
    job_id: str
    symbol: str
    status: str


class HorizonPred(BaseModel):
    direction: str
    prob: float


class FeatureImportance(BaseModel):
    feature: str
    importance: float


class MlResult(BaseModel):
    prediction: str
    direction: str
    confidence: float
    accuracy: float
    top_features: list[FeatureImportance]
    n_train: int
    n_test: int
    horizon: dict[str, HorizonPred]
    model_accs: dict[str, float]
    conf_tier: dict[str, str]
    up_prob: float
    dn_prob: float
    sentiment: dict[str, Any]
    lstm_prob: float
    walk_fwd_acc: float
    ensemble_size: int
    active_models: str
    shap: dict[str, Any]
    predicted_price: float | None


class JobStatusResponse(BaseModel):
    job_id: str
    symbol: str
    status: str
    started_at: float
    finished_at: float | None
    result: MlResult | None = None
    error: str | None = None


class LstmForecastResponse(BaseModel):
    available: bool
    symbol: str | None = None
    model: str | None = None
    last_close: float | None = None
    predicted_close: float | None = None
    expected_change_pct: float | None = None
    trained_points: int | None = None
    test_mse_scaled: float | None = None
    reason: str | None = None


class EvalResponse(BaseModel):
    symbol: str
    walk_fwd_acc: float
    model_accs: dict[str, float]
    n_train: int
    n_test: int
    fold_scores: list[float]
