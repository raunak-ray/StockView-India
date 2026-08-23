"""Ensemble engine — verbatim port of run_ml (app.py:2650-2940) and the
Bi-LSTM classifier LSTMNet (app.py:2273-2292). The st.cache_data decorator
is replaced by the service-layer Redis TTL cache.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

from app.modules.ml import capabilities as caps
from app.modules.ml.features import TREE_FEATS, build_features
from app.modules.sentiment.service import get_sentiment_score

logger = logging.getLogger(__name__)

# ── Bi-LSTM classifier (torch optional — parity app.py:2273) ────────────────
if caps.TORCH_OK:

    class LSTMNet(caps.nn.Module):  # type: ignore[misc]
        def __init__(self, input_size, hidden=64, layers=2, dropout=0.3):
            super().__init__()
            self.lstm = caps.nn.LSTM(
                input_size, hidden, num_layers=layers,
                batch_first=True, bidirectional=True,
                dropout=dropout if layers > 1 else 0.0,
            )
            self.norm = caps.nn.LayerNorm(hidden * 2)
            self.fc = caps.nn.Sequential(
                caps.nn.Linear(hidden * 2, 32), caps.nn.ReLU(),
                caps.nn.Dropout(dropout), caps.nn.Linear(32, 2),
            )

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(self.norm(out[:, -1, :]))


def run_ml(
    df: pd.DataFrame,
    sector: str = "",
    headlines: list | None = None,
    use_lstm: bool = False,
    use_finbert: bool = False,
) -> dict[str, Any] | None:
    """
    Professional Ensemble AI Engine v2.0 (parity app.py:2650).
    Models: XGBoost · LightGBM · CatBoost · LSTM · FinBERT sentiment
    Fallback: RF + GBM + LR if boosters not installed.
    Chronological 80/20 split — no lookahead bias.
    """
    req = ["RSI", "MACD", "M_SIG", "M_HIS", "ATR", "High", "Low", "Open", "Close", "Volume"]
    if any(c not in df.columns for c in req):
        return None

    fd = build_features(df, sector=sector)
    fd["Tgt1"] = (fd["Close"].shift(-1) > fd["Close"]).astype(int)
    fd["Tgt3"] = (fd["Close"].shift(-3) > fd["Close"]).astype(int)
    fd["Tgt5"] = (fd["Close"].shift(-5) > fd["Close"]).astype(int)
    fd.replace([np.inf, -np.inf], np.nan, inplace=True)
    fd.dropna(inplace=True)
    if len(fd) < 100:
        return None

    avail_feats = [f for f in TREE_FEATS if f in fd.columns]
    X_all = fd[avail_feats].values.astype(np.float32)
    y_all = fd["Tgt5"].values  # primary: 5-bar horizon

    sp = int(len(X_all) * 0.80)
    Xtr, Xte = X_all[:sp], X_all[sp:]
    ytr, yte = y_all[:sp], y_all[sp:]
    sc_ = StandardScaler()
    Xtr_s = sc_.fit_transform(Xtr)
    Xte_s = sc_.transform(Xte)
    X_pred = sc_.transform(X_all[-1].reshape(1, -1))

    probs_list: list[tuple[float, int]] = []  # (up_prob, weight)
    model_accs: dict[str, float] = {}
    rf_: RandomForestClassifier | None = None

    # ── XGBoost ──────────────────────────────────────────────────
    if caps.XGB_OK:
        try:
            xgb_m = caps.xgb.XGBClassifier(
                n_estimators=300, max_depth=5, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                eval_metric="logloss", random_state=42, n_jobs=-1, verbosity=0,
            )
            xgb_m.fit(Xtr_s, ytr, eval_set=[(Xte_s, yte)], verbose=False)
            xgb_acc = xgb_m.score(Xte_s, yte)
            xgb_up = float(xgb_m.predict_proba(X_pred)[0][1])
            probs_list.append((xgb_up, 4))
            model_accs["XGB"] = round(xgb_acc * 100, 1)
        except Exception:  # noqa: BLE001, S110 - best-effort model, parity
            pass

    # ── LightGBM ─────────────────────────────────────────────────
    if caps.LGB_OK:
        try:
            lgb_m = caps.lgb.LGBMClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, num_leaves=31,
                random_state=42, n_jobs=-1, verbose=-1,
            )
            lgb_m.fit(Xtr_s, ytr, eval_set=[(Xte_s, yte)])
            lgb_acc = lgb_m.score(Xte_s, yte)
            lgb_up = float(lgb_m.predict_proba(X_pred)[0][1])
            probs_list.append((lgb_up, 4))
            model_accs["LGBM"] = round(lgb_acc * 100, 1)
        except Exception:  # noqa: BLE001, S110
            pass

    # ── CatBoost ─────────────────────────────────────────────────
    if caps.CAT_OK:
        try:
            cat_m = caps.CatBoostClassifier(
                iterations=300, depth=6, learning_rate=0.05,
                random_seed=42, verbose=0, eval_metric="Accuracy",
            )
            sect_idx = [avail_feats.index("SECTOR_ID")] if "SECTOR_ID" in avail_feats else []
            cat_m.fit(Xtr_s, ytr, eval_set=(Xte_s, yte), cat_features=sect_idx)
            cat_acc = cat_m.score(Xte_s, yte)
            cat_up = float(cat_m.predict_proba(X_pred)[0][1])
            probs_list.append((cat_up, 3))
            model_accs["CAT"] = round(cat_acc * 100, 1)
        except Exception:  # noqa: BLE001, S110
            pass

    # ── Fallback: RF + GBM + LR ──────────────────────────────────
    if not probs_list:
        rf_ = RandomForestClassifier(
            n_estimators=200, max_depth=7,
            min_samples_leaf=5, random_state=42, n_jobs=-1,
        )
        gbm_ = GradientBoostingClassifier(
            n_estimators=150, max_depth=4,
            learning_rate=0.05, subsample=0.8, random_state=42,
        )
        lr_ = LogisticRegression(C=1.0, max_iter=500, random_state=42)
        for m_, w_, k_ in [(rf_, 3, "RF"), (gbm_, 3, "GBM"), (lr_, 1, "LR")]:
            m_.fit(Xtr_s, ytr)
            probs_list.append((float(m_.predict_proba(X_pred)[0][1]), w_))
            model_accs[k_] = round(m_.score(Xte_s, yte) * 100, 1)
    else:
        # Keep RF for feature importance
        rf_ = RandomForestClassifier(
            n_estimators=150, max_depth=7,
            min_samples_leaf=5, random_state=42, n_jobs=-1,
        )
        rf_.fit(Xtr_s, ytr)

    # ── LSTM (optional, slower) ──────────────────────────────────
    lstm_up = 0.5
    if use_lstm and caps.TORCH_OK and len(fd) >= 150:
        try:
            lstm_feats = [
                f for f in ["RN", "MD", "BBP", "BBW", "R1", "R3", "VOL5", "VR",
                            "AN", "BODY", "MOM5", "MOM10", "SX"]
                if f in fd.columns
            ]
            X_lstm = fd[lstm_feats].values.astype(np.float32)
            y_lstm = fd["Tgt5"].values
            sc_l = StandardScaler()
            Xs_l = sc_l.fit_transform(X_lstm)
            seq_len = 20
            wins, labs = [], []
            for i in range(seq_len, len(Xs_l)):
                wins.append(Xs_l[i - seq_len:i])
                labs.append(y_lstm[i])
            W = np.array(wins, dtype=np.float32)
            L = np.array(labs)
            sp2 = int(len(W) * 0.8)
            Wtr = caps.torch.from_numpy(W[:sp2])
            Ytr = caps.torch.tensor(L[:sp2], dtype=caps.torch.long)
            Wte = caps.torch.from_numpy(W[sp2:])
            Yte = caps.torch.tensor(L[sp2:], dtype=caps.torch.long)
            net = LSTMNet(input_size=W.shape[2])
            opt = caps.torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
            crit = caps.nn.CrossEntropyLoss()
            net.train()
            for _ in range(40):
                opt.zero_grad()
                loss = crit(net(Wtr), Ytr)
                loss.backward()
                caps.torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
                opt.step()
            net.eval()
            with caps.torch.no_grad():
                lstm_acc = (net(Wte).argmax(1) == Yte).float().mean().item()
                win_pred = caps.torch.from_numpy(
                    Xs_l[-seq_len:].reshape(1, seq_len, -1).astype(np.float32)
                )
                lstm_up = float(caps.torch.softmax(net(win_pred), 1)[0][1].item())
            probs_list.append((lstm_up, 2))
            model_accs["LSTM"] = round(lstm_acc * 100, 1)
        except Exception:  # noqa: BLE001, S110
            pass

    # ── FinBERT sentiment bias ───────────────────────────────────
    sentiment: dict[str, Any] = {"score": 0.0, "label": "NEUTRAL", "detail": []}
    sent_bias = 0.0
    if use_finbert and headlines:
        sentiment = get_sentiment_score(headlines)
        sent_bias = float(np.clip(sentiment["score"] * 0.10, -0.05, 0.05))

    # ── Weighted ensemble ────────────────────────────────────────
    total_w = sum(w for _, w in probs_list)
    ens_up = float(np.clip(sum(p * w for p, w in probs_list) / total_w + sent_bias, 0.0, 1.0))
    ens_dn = 1.0 - ens_up
    pc = 1 if ens_up > 0.5 else 0
    conf = float(max(ens_up, ens_dn)) * 100

    # ── Multi-horizon predictions ────────────────────────────────
    horizon_preds: dict[str, Any] = {}
    for h, col in [(1, "Tgt1"), (3, "Tgt3"), (5, "Tgt5")]:
        yh = fd[col].values
        if len(np.unique(yh)) < 2:
            continue
        if caps.XGB_OK:
            try:
                hm = caps.xgb.XGBClassifier(
                    n_estimators=200, max_depth=4, learning_rate=0.05,
                    eval_metric="logloss", random_state=42, n_jobs=-1, verbosity=0,
                )
                hm.fit(Xtr_s, yh[:sp])
                ph = float(hm.predict_proba(X_pred)[0][1])
            except Exception:  # noqa: BLE001
                ph = float(rf_.predict_proba(X_pred)[0][1]) if rf_ else 0.5
        else:
            hm = RandomForestClassifier(
                n_estimators=120, max_depth=6, random_state=42, n_jobs=-1
            )
            hm.fit(Xtr_s, yh[:sp])
            ph = float(hm.predict_proba(X_pred)[0][1])
        horizon_preds[str(h)] = {"direction": "up" if ph > 0.5 else "down", "prob": round(ph * 100, 1)}

    # ── Feature importance ───────────────────────────────────────
    imps = sorted(zip(avail_feats, rf_.feature_importances_), key=lambda x: -x[1])[:6] if rf_ else []

    # ── SHAP explainability (optional — parity app.py:2860) ──────
    shap_result: dict[str, Any] = {"ok": False, "error": "shap not installed"}
    if caps.SHAP_OK and rf_ is not None:
        try:
            _shap_exp = caps.shap.TreeExplainer(rf_)
            _shap_vals_r = _shap_exp.shap_values(Xte_s)
            _shap_vals = _shap_vals_r[1] if isinstance(_shap_vals_r, list) else _shap_vals_r
            _ev = _shap_exp.expected_value
            _base_val = float(_ev[1]) if hasattr(_ev, "__len__") else float(_ev)
            _shap_lat_r = _shap_exp.shap_values(X_pred)
            _shap_lat = _shap_lat_r[1][0] if isinstance(_shap_lat_r, list) else _shap_lat_r[0]
            _mean_abs = np.abs(_shap_vals).mean(axis=0)
            shap_result = {
                "ok": True,
                "importance": sorted(
                    zip(avail_feats, _mean_abs.tolist()), key=lambda x: -x[1]
                )[:10],
                "waterfall": sorted(
                    zip(avail_feats, _shap_lat.tolist()), key=lambda x: -abs(x[1])
                )[:10],
                "base_value": _base_val,
            }
        except Exception as _shap_err:  # noqa: BLE001 - explainability is best-effort
            shap_result = {"ok": False, "error": str(_shap_err)}

    # ── Walk-forward accuracy (TimeSeriesSplit) ──────────────────
    tscv = TimeSeriesSplit(n_splits=5)
    wf_accs = []
    for tr_i, te_i in tscv.split(X_all):
        _m = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42, n_jobs=-1)
        _sc = StandardScaler()
        _m.fit(_sc.fit_transform(X_all[tr_i]), y_all[tr_i])
        wf_accs.append(_m.score(_sc.transform(X_all[te_i]), y_all[te_i]))
    wf_acc = float(np.mean(wf_accs)) * 100

    # ── Confidence tier ──────────────────────────────────────────
    if conf >= 75:
        tier = ("HIGH", "up")
    elif conf >= 60:
        tier = ("MEDIUM", "gold")
    else:
        tier = ("LOW", "down")

    active = "+".join(model_accs.keys())

    # ── Predicted next candle price (ATR-scaled by conviction) ───
    try:
        _last_close = float(fd["Close"].iloc[-1])
        _atr_now = float(fd["ATR"].iloc[-1]) if "ATR" in fd.columns else _last_close * 0.015
        _conviction = abs(ens_up - 0.5) * 2
        _expected_move = _atr_now * (0.5 + 0.5 * _conviction)
        _pred_price = _last_close + (_expected_move if pc == 1 else -_expected_move)
        _pred_price = round(_pred_price, 2)
    except Exception:  # noqa: BLE001
        _pred_price = None

    return {
        "prediction": "UP" if pc == 1 else "DOWN",
        "direction": "up" if pc == 1 else "down",
        "confidence": round(conf, 1),
        "accuracy": round(wf_acc, 1),
        "top_features": [{"feature": f, "importance": round(float(i), 4)} for f, i in imps],
        "n_train": sp,
        "n_test": len(Xte),
        "horizon": horizon_preds,
        "model_accs": model_accs,
        "conf_tier": {"tier": tier[0], "tone": tier[1]},
        "up_prob": round(ens_up * 100, 1),
        "dn_prob": round(ens_dn * 100, 1),
        "sentiment": sentiment,
        "lstm_prob": round(lstm_up * 100, 1),
        "walk_fwd_acc": round(wf_acc, 1),
        "ensemble_size": len(probs_list),
        "active_models": active,
        "shap": shap_result,
        "predicted_price": _pred_price,
    }
