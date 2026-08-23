"""Feature engineering — verbatim port of _build_features (app.py:2581-2648)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_features(df: pd.DataFrame, sector: str = "") -> pd.DataFrame:
    fd = df.copy()
    # Returns
    fd["R1"] = fd["Close"].pct_change(1)
    fd["R3"] = fd["Close"].pct_change(3)
    fd["R5"] = fd["Close"].pct_change(5)
    fd["R10"] = fd["Close"].pct_change(10)
    fd["R21"] = fd["Close"].pct_change(21)
    fd["LR1"] = np.log(fd["Close"] / fd["Close"].shift(1).replace(0, np.nan))
    fd["LR5"] = np.log(fd["Close"] / fd["Close"].shift(5).replace(0, np.nan))
    # Volatility
    fd["VOL5"] = fd["LR1"].rolling(5).std()
    fd["VOL10"] = fd["LR1"].rolling(10).std()
    fd["VOL21"] = fd["LR1"].rolling(21).std()
    # Volume
    fd["VR"] = fd["Volume"] / (fd["Volume"].rolling(20).mean() + 1e-9)
    fd["OBV"] = (np.sign(fd["Close"].diff()) * fd["Volume"]).fillna(0).cumsum()
    fd["OBV_SLP"] = fd["OBV"].diff(5)
    # Bollinger
    if "BB_H" in fd.columns and "BB_L" in fd.columns and "SMA_20" in fd.columns:
        fd["BBW"] = (fd["BB_H"] - fd["BB_L"]) / (fd["SMA_20"] + 1e-9)
        fd["BBP"] = (fd["Close"] - fd["BB_L"]) / (fd["BB_H"] - fd["BB_L"] + 1e-9)
    else:
        fd["BBW"] = 0
        fd["BBP"] = 0.5
    # MACD
    if "MACD" in fd.columns and "M_SIG" in fd.columns:
        fd["MD"] = fd["MACD"] - fd["M_SIG"]
        fd["MH"] = fd["M_HIS"] if "M_HIS" in fd.columns else fd["MD"].diff()
    else:
        fd["MD"] = 0
        fd["MH"] = 0
    # RSI & ATR
    fd["RN"] = fd["RSI"] / 100 if "RSI" in fd.columns else 0.5
    fd["AN"] = fd["ATR"] / (fd["Close"] + 1e-9) if "ATR" in fd.columns else 0
    fd["ATR_RATIO"] = fd["ATR"] / fd["Close"] if "ATR" in fd.columns else 0
    # Candle structure
    fd["HLP"] = (fd["High"] - fd["Low"]) / (fd["Close"] + 1e-9)
    fd["BODY"] = abs(fd["Close"] - fd["Open"]) / (fd["High"] - fd["Low"] + 1e-9)
    fd["UWK"] = (fd["High"] - fd[["Close", "Open"]].max(axis=1)) / (fd["High"] - fd["Low"] + 1e-9)
    fd["LWK"] = (fd[["Close", "Open"]].min(axis=1) - fd["Low"]) / (fd["High"] - fd["Low"] + 1e-9)
    fd["IS_BULL"] = (fd["Close"] > fd["Open"]).astype(int)
    # Momentum
    fd["MOM5"] = fd["Close"] / (fd["Close"].shift(5) + 1e-9) - 1
    fd["MOM10"] = fd["Close"] / (fd["Close"].shift(10) + 1e-9) - 1
    fd["MOM21"] = fd["Close"] / (fd["Close"].shift(21) + 1e-9) - 1
    # SMA cross
    if "SMA_20" in fd.columns and "SMA_50" in fd.columns:
        fd["SX"] = (fd["SMA_20"] - fd["SMA_50"]) / (fd["SMA_50"] + 1e-9)
        fd["PRICE_SMA20"] = (fd["Close"] - fd["SMA_20"]) / (fd["SMA_20"] + 1e-9)
        fd["PRICE_SMA50"] = (fd["Close"] - fd["SMA_50"]) / (fd["SMA_50"] + 1e-9)
    else:
        fd["SX"] = 0
        fd["PRICE_SMA20"] = 0
        fd["PRICE_SMA50"] = 0
    # VWAP
    fd["VWAP_DIST"] = (
        (fd["Close"] - fd["VWAP"]) / (fd["VWAP"] + 1e-9) if "VWAP" in fd.columns else 0
    )
    # Sector
    sector_map = {
        "Technology": 0, "Financial Services": 1, "Healthcare": 2, "Energy": 3,
        "Materials": 4, "Consumer Cyclical": 5, "Consumer Defensive": 6,
        "Industrials": 7, "Utilities": 8, "Real Estate": 9,
        "Communication Services": 10,
    }
    fd["SECTOR_ID"] = sector_map.get(sector, -1)
    return fd


TREE_FEATS = [
    "RN", "MD", "MH", "BBP", "BBW", "R1", "R3", "R5", "R10", "R21",
    "LR1", "LR5", "VOL5", "VOL10", "VOL21", "VR", "OBV_SLP",
    "AN", "ATR_RATIO", "HLP", "BODY", "UWK", "LWK", "IS_BULL",
    "MOM5", "MOM10", "MOM21", "SX", "PRICE_SMA20", "PRICE_SMA50", "VWAP_DIST",
]
