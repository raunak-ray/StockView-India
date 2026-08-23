from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.modules.analytics.service import add_indicators
from app.modules.ml import capabilities as caps
from app.modules.ml.ensemble import run_ml
from app.modules.ml.features import TREE_FEATS, build_features


def enriched_df(n: int = 300, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0.05, 1, n))
    df = pd.DataFrame(
        {
            "Open": close + rng.normal(0, 0.2, n),
            "High": close + np.abs(rng.normal(0.6, 0.2, n)),
            "Low": close - np.abs(rng.normal(0.6, 0.2, n)),
            "Close": close,
            "Volume": rng.integers(1e5, 5e6, n).astype(float),
        },
        index=pd.date_range("2024-01-01", periods=n, freq="B"),
    )
    return add_indicators(df)


# ── Features ──────────────────────────────────────────────────────────────────


def test_build_features_columns_and_ranges():
    fd = build_features(enriched_df(), sector="Technology")
    for col in TREE_FEATS:
        assert col in fd.columns, f"missing {col}"
    assert fd["SECTOR_ID"].iloc[-1] == 0  # Technology maps to 0
    rn = fd["RN"].dropna()
    assert rn.between(0, 1).all()
    fd2 = build_features(enriched_df(), sector="Unknown")
    assert fd2["SECTOR_ID"].iloc[-1] == -1


def test_build_features_unknown_sector_maps_to_minus_one():
    fd = build_features(enriched_df(), sector="")
    assert (fd["SECTOR_ID"] == -1).all()


# ── Ensemble (contract test: fallback works without heavy deps) ───────────────


def test_run_ml_fallback_returns_valid_prediction():
    """With boosters absent the RF/GBM/LR path must still produce a verdict."""
    result = run_ml(enriched_df(), sector="Financial Services")
    assert result is not None
    assert result["direction"] in {"up", "down"}
    assert 0.0 <= result["up_prob"] <= 100.0
    assert result["up_prob"] + result["dn_prob"] == pytest.approx(100.0, abs=0.2)
    assert 50.0 <= result["confidence"] <= 100.0
    assert result["n_train"] + result["n_test"] > 150
    # At least one model reported accuracy, fallback names when no boosters
    if not (caps.XGB_OK or caps.LGB_OK or caps.CAT_OK):
        assert set(result["model_accs"]) == {"RF", "GBM", "LR"}
    assert result["conf_tier"]["tier"] in {"HIGH", "MEDIUM", "LOW"}


def test_run_ml_horizons_and_price():
    result = run_ml(enriched_df())
    assert set(result["horizon"]) <= {"1", "3", "5"}
    for h in result["horizon"].values():
        assert h["direction"] in {"up", "down"}
        assert 0 <= h["prob"] <= 100
    assert result["predicted_price"] is None or result["predicted_price"] > 0
    assert len(result["top_features"]) <= 6


def test_run_ml_rejects_short_history():
    assert run_ml(enriched_df(n=90)) is None


def test_run_ml_chronological_split():
    """The 80/20 split leaves a real holdout; ordering is enforced by the
    code path (first sp rows train, last rows test — never shuffled)."""
    result = run_ml(enriched_df())
    assert result is not None
    assert result["n_test"] > 0
    ratio = result["n_train"] / (result["n_train"] + result["n_test"])
    assert 0.75 <= ratio <= 0.85


# ── Capabilities ──────────────────────────────────────────────────────────────


def test_capability_map_shapes():
    m = caps.capability_map()
    assert m["sklearn"] is True
    assert all(isinstance(v, bool) for v in m.values())
    ens = caps.active_ensemble()
    assert len(ens) >= 3  # boosters or fallback trio


def test_walk_forward_accuracy_is_percentage():
    result = run_ml(enriched_df())
    assert 0.0 <= result["walk_fwd_acc"] <= 100.0
