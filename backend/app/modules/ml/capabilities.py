"""Optional heavy-dependency capability flags (parity app.py:24-55).

Everything here degrades gracefully: the ensemble always has the
scikit-learn fallback path, and each endpoint reports what is actually
available via GET /ml/capabilities.
"""

from __future__ import annotations

try:  # pragma: no cover - depends on optional install
    import xgboost as xgb

    XGB_OK = True
except ImportError:
    xgb = None  # type: ignore[assignment,no-redef]
    XGB_OK = False

try:  # pragma: no cover
    import lightgbm as lgb

    LGB_OK = True
except ImportError:
    lgb = None  # type: ignore[assignment,no-redef]
    LGB_OK = False

try:  # pragma: no cover
    from catboost import CatBoostClassifier

    CAT_OK = True
except ImportError:
    CatBoostClassifier = None  # type: ignore[assignment,no-redef]
    CAT_OK = False

try:  # pragma: no cover
    import torch
    from torch import nn

    TORCH_OK = True
except ImportError:
    torch = None  # type: ignore[assignment,no-redef]
    nn = None  # type: ignore[assignment,no-redef]
    TORCH_OK = False

try:  # pragma: no cover
    import shap

    SHAP_OK = True
except ImportError:
    shap = None  # type: ignore[assignment,no-redef]
    SHAP_OK = False


def capability_map() -> dict[str, bool]:
    return {
        "sklearn": True,  # core dependency — fallback ensemble always available
        "xgboost": XGB_OK,
        "lightgbm": LGB_OK,
        "catboost": CAT_OK,
        "torch": TORCH_OK,
        "shap": SHAP_OK,
    }


def active_ensemble() -> list[str]:
    """Model names that will vote, given what is installed."""
    names: list[str] = []
    if XGB_OK:
        names.append("XGB")
    if LGB_OK:
        names.append("LGBM")
    if CAT_OK:
        names.append("CAT")
    if not names:
        names = ["RF", "GBM", "LR"]
    return names
