"""ML service — orchestration: data -> ensemble / price LSTM, with caching."""

from __future__ import annotations

import logging
from typing import Any

import anyio.to_thread

from app.core.cache import cache_get, cache_set
from app.modules.analytics import service as analytics
from app.modules.market_data import service as market_data
from app.modules.ml import capabilities as caps
from app.modules.ml import ensemble, price_lstm
from app.modules.sentiment.service import get_headlines

logger = logging.getLogger(__name__)

PREDICT_TTL = 900  # 15 min — training result is stable for a while
LSTM_TTL = 900
MIN_ROWS = 120


async def predict(symbol: str, use_lstm: bool = False) -> dict[str, Any]:
    """Full ensemble prediction. CPU-bound work runs in a worker thread."""
    key = f"ml:predict:{symbol}:{int(use_lstm)}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    candles = await market_data.get_history(symbol, "1d", "2y")
    df = analytics.candles_to_df(candles)
    df = analytics.add_indicators(df)
    if len(df) < MIN_ROWS:
        from fastapi import HTTPException, status

        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Not enough price history to train a model",
        )

    info = await market_data.get_info(symbol)
    sector = str(info.get("sector", "")) if isinstance(info, dict) else ""
    headlines = await get_headlines(symbol, max_items=8)

    result = await anyio.to_thread.run_sync(
        ensemble.run_ml, df, sector, headlines, use_lstm, True
    )
    if result is None:
        from fastapi import HTTPException, status

        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Not enough usable rows after indicator warm-up",
        )
    await cache_set(key, result, PREDICT_TTL)
    return result


async def lstm_forecast(symbol: str) -> dict[str, Any]:
    """Next-day price forecast from the per-symbol PyTorch LSTM (plan/lstm.py)."""
    if not caps.TORCH_OK:
        return {"available": False, "reason": "torch not installed"}

    key = f"ml:lstm-forecast:{symbol}"
    cached = await cache_get(key)
    if cached is not None:
        return cached

    candles = await market_data.get_history(symbol, "1d", "2y")
    df = analytics.candles_to_df(candles)
    closes = df["Close"].dropna().values.astype(float)

    result = await anyio.to_thread.run_sync(price_lstm.forecast_from_closes, symbol, closes)
    if result.get("available"):
        await cache_set(key, result, LSTM_TTL)
    return result


async def evaluate(symbol: str) -> dict[str, Any]:
    """Walk-forward accuracy view over the cached ensemble prediction."""
    result = await predict(symbol)
    return {
        "symbol": symbol,
        "walk_fwd_acc": result["walk_fwd_acc"],
        "model_accs": result["model_accs"],
        "n_train": result["n_train"],
        "n_test": result["n_test"],
        "fold_scores": [],  # reserved for per-fold detail (future work)
    }


def risk_note() -> dict[str, Any]:
    """Deterministic disclaimer that ships with every prediction."""
    return {
        "note": "Model estimates, not guarantees. Trained on historical prices only.",
    }
