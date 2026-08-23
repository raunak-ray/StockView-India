"""Next-day price LSTM — PyTorch port of plan/lstm.py.

The uploaded reference script used Keras/TensorFlow; we implement the exact
same design (60-day lookback on Close, MinMax scaling, two stacked LSTM
layers of 50 units, dense head) in PyTorch because torch is already an
optional extra of this project (`.ml-heavy`) — no new 2 GB dependency.

Trained per symbol on demand and cached in memory for the process lifetime.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from app.modules.ml import capabilities as caps

logger = logging.getLogger(__name__)

LOOKBACK = 60
EPOCHS = 12
BATCH = 32
TRAIN_TTL = 24 * 3600  # retrain at most daily

_models: dict[str, dict[str, Any]] = {}  # symbol -> {net, scaler, trained_at, points}


class _PriceLSTM(caps.nn.Module):  # type: ignore[misc]
    """Two stacked LSTM(50) cells + linear head — mirrors plan/lstm.py."""

    def __init__(self, features: int = 1):
        super().__init__()
        self.lstm = caps.nn.LSTM(
            features, 50, num_layers=2, batch_first=True, dropout=0.1
        )
        self.head = caps.nn.Sequential(
            caps.nn.Linear(50, 1),
        )

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :]).squeeze(-1)


def _train_sync(closes: np.ndarray) -> dict[str, Any]:
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(closes.reshape(-1, 1)).astype(np.float32)

    xs, ys = [], []
    for i in range(LOOKBACK, len(scaled)):
        xs.append(scaled[i - LOOKBACK:i])
        ys.append(scaled[i])
    X = np.array(xs, dtype=np.float32)
    Y = np.array(ys, dtype=np.float32)

    sp = int(len(X) * 0.8)  # chronological split — never shuffle time series
    Xtr = caps.torch.from_numpy(X[:sp])
    Ytr = caps.torch.from_numpy(Y[:sp])
    Xte = caps.torch.from_numpy(X[sp:])
    Yte = caps.torch.from_numpy(Y[sp:])

    caps.torch.manual_seed(42)
    net = _PriceLSTM()
    opt = caps.torch.optim.Adam(net.parameters(), lr=1e-3)
    crit = caps.nn.MSELoss()
    net.train()
    n = len(Xtr)
    for _ in range(EPOCHS):
        perm = caps.torch.randperm(n)
        for s in range(0, n, BATCH):
            idx = perm[s:s + BATCH]
            opt.zero_grad()
            loss = crit(net(Xtr[idx]), Ytr[idx])
            loss.backward()
            opt.step()
    net.eval()
    with caps.torch.no_grad():
        test_mse = float(crit(net(Xte), Yte).item())
        last = caps.torch.from_numpy(scaled[-LOOKBACK:].reshape(1, LOOKBACK, 1))
        pred_scaled = float(net(last).item())
    pred_price = float(scaler.inverse_transform([[pred_scaled]])[0][0])
    return {
        "net": net,
        "scaler": scaler,
        "trained_at": time.time(),
        "points": len(X),
        "test_mse_scaled": test_mse,
        "last_prediction": pred_price,
    }


def forecast_from_closes(symbol: str, closes: np.ndarray) -> dict[str, Any]:
    """Train (or reuse) the per-symbol price LSTM and predict tomorrow's close."""
    if not caps.TORCH_OK:
        return {"available": False, "reason": "torch not installed"}
    closes = closes.astype(float)
    if len(closes) < LOOKBACK + 60:  # need a meaningful training set
        return {"available": False, "reason": "not enough history"}

    cached = _models.get(symbol)
    if cached and time.time() - cached["trained_at"] < TRAIN_TTL:
        with caps.torch.no_grad():
            scaler = cached["scaler"]
            scaled = scaler.transform(closes.reshape(-1, 1)).astype(np.float32)
            last = caps.torch.from_numpy(scaled[-LOOKBACK:].reshape(1, LOOKBACK, 1))
            pred = float(cached["net"](last).item())
            pred_price = float(scaler.inverse_transform([[pred]])[0][0])
        points, mse = cached["points"], cached["test_mse_scaled"]
    else:
        try:
            trained = _train_sync(closes)
            _models[symbol] = trained
            pred_price = trained["last_prediction"]
            points, mse = trained["points"], trained["test_mse_scaled"]
        except Exception as exc:  # noqa: BLE001 - degrade, never 500
            logger.warning("price LSTM training failed for %s: %s", symbol, exc)
            return {"available": False, "reason": "training failed"}

    last_close = float(closes[-1])
    change_pct = ((pred_price - last_close) / last_close) * 100 if last_close else 0.0
    return {
        "available": True,
        "symbol": symbol,
        "model": f"pytorch lstm · {LOOKBACK}-day lookback",
        "last_close": round(last_close, 2),
        "predicted_close": round(pred_price, 2),
        "expected_change_pct": round(change_pct, 2),
        "trained_points": points,
        "test_mse_scaled": round(mse, 6),
    }


def forecast_from_df(symbol: str, df: pd.DataFrame) -> dict[str, Any]:
    return forecast_from_closes(symbol, df["Close"].dropna().values)
