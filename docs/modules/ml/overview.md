# ML — what it is

The ML module predicts **next-day and 5-day price direction** for any symbol
using a stacked ensemble of machine learning models, with an optional PyTorch
LSTM that predicts the actual next-day close price.

It is the heaviest module by far — multiple model families, ~30 features, walk-
forward validation, SHAP explainability, and a background-job system so long
training runs do not block the API.

This page explains the high level. The how-it-works page walks through every
stage. The implementation page is for someone reading the code.

## What you can do with it

- **Get a direction prediction** for a symbol (UP / DOWN) with confidence,
  per-model accuracy, top contributing features, and predicted next price.
- **Check installed capabilities** — which model libraries are available.
- **Get a next-day price forecast** from the standalone PyTorch LSTM.
- **See model evaluation** — walk-forward accuracy, train/test sizes.
- **Run training as a background job** — POST starts a job, GET polls its
  status; the result also lands in Redis so repeat calls are instant.

## The models

| Model | Library | Optional? | Role |
|---|---|---|---|
| XGBoost | `xgboost` | yes | Direction classifier, weight 4 |
| LightGBM | `lightgbm` | yes | Direction classifier, weight 4 |
| CatBoost | `catboost` | yes | Direction classifier, weight 3 |
| LSTM (direction) | `torch` | yes | Direction classifier, weight 2 |
| FinBERT sentiment | `transformers` | yes | +0–5% bias on the ensemble probability |
| Random Forest | `sklearn` | core | Always present; used for feature importance + fallback |
| Gradient Boosting | `sklearn` | core | Fallback direction classifier |
| Logistic Regression | `sklearn` | core | Fallback direction classifier |
| LSTM (price) | `torch` | yes | Next-day close price regression |

The "core" models ship with the project's main dependencies. The "optional"
ones are checked at runtime — see `capabilities.py`. The frontend shows which
ensemble actually ran via the `capabilities` endpoint and the `active_models`
field in the response.

### Fallback rule

If none of XGBoost / LightGBM / CatBoost is installed, the ensemble drops to
RF + GBM + LR. The app never breaks because of a missing optional library.

If PyTorch is not installed, the LSTM is silently skipped. The price LSTM
returns `{ available: false, reason: "torch not installed" }`.

## The features

`features.build_features()` derives ~30 numeric columns from the indicator-
enriched price frame. Categories:

| Category | Columns | Meaning |
|---|---|---|
| Returns | `R1, R3, R5, R10, R21, LR1, LR5` | Percentage and log returns over various windows |
| Volatility | `VOL5, VOL10, VOL21` | Rolling std of log returns |
| Volume | `VR, OBV_SLP` | Volume ratio vs 20-day mean, OBV slope |
| Bollinger | `BBP, BBW` | Position within bands, band width |
| MACD | `MD, MH` | MACD minus signal, MACD histogram |
| RSI / ATR | `RN, AN, ATR_RATIO` | RSI / 100, ATR / close, ATR / close |
| Candle shape | `HLP, BODY, UWK, LWK, IS_BULL` | Range, body ratio, upper/lower wicks, bullish flag |
| Momentum | `MOM5, MOM10, MOM21` | 5/10/21-day momentum |
| SMA cross | `SX, PRICE_SMA20, PRICE_SMA50` | SMA20 vs SMA50, price distance |
| VWAP | `VWAP_DIST` | Price vs VWAP (0 if not present) |
| Sector | `SECTOR_ID` | Yahoo sector as integer (–1 if unknown) |

The list of features that actually go into the tree models is `TREE_FEATS`
(31 columns). Each row is one trading day. The model predicts whether the
close 5 days later will be higher (`Tgt5 = 1`) or lower (`Tgt5 = 0`).

## The targets

Three binary targets at different horizons:

| Column | Question | Default horizon |
|---|---|---|
| `Tgt1` | Will close tomorrow be higher? | 1 day |
| `Tgt3` | Will close in 3 days be higher? | 3 days |
| `Tgt5` | Will close in 5 days be higher? | 5 days (primary) |

The ensemble trains on `Tgt5` and reports per-horizon predictions for `1` and
`3` day.

## Train / test split

Chronological 80/20 split. No shuffling, no random folds — that would leak
future information into the past and inflate accuracy. The test set is always
the most recent 20% of bars.

Walk-forward validation uses `sklearn.model_selection.TimeSeriesSplit` with 5
splits. The reported `walk_fwd_acc` is the mean of these 5 out-of-sample
accuracies.

## The confidence tiers

| Confidence % | Tier | UI tone |
|---|---|---|
| ≥ 75 | HIGH | up (green) |
| 60–74 | MEDIUM | gold (yellow) |
| < 60 | LOW | down (red) |

Confidence is `max(ens_up, 1 - ens_up) × 100`. A 50/50 split gives 50% — LOW
tier. The UI shows this honestly so the user knows the model is guessing.

## A real example

You open INFY. `/ml/predict` returns:

```json
{
  "prediction": "UP",
  "direction": "up",
  "confidence": 62.0,
  "accuracy": 54.5,
  "up_prob": 62.0,
  "dn_prob": 38.0,
  "horizon": {
    "1": {"direction": "up", "prob": 58.3},
    "3": {"direction": "up", "prob": 60.1},
    "5": {"direction": "up", "prob": 62.0}
  },
  "model_accs": {"XGB": 56.2, "LGBM": 55.8, "CAT": 54.9},
  "walk_fwd_acc": 54.5,
  "ensemble_size": 3,
  "active_models": "XGB+LGBM+CAT",
  "predicted_price": 1842.50,
  "top_features": [
    {"feature": "R5", "importance": 0.18},
    {"feature": "RSI_normalised", "importance": 0.14},
    {"feature": "BBP", "importance": 0.11}
  ]
}
```

INFY up by 62% confidence, three models vote, all 54–56% accurate on the
walk-forward check. Confidence is MEDIUM (gold). LSTM predicts next-day close
at ₹1,842.

## What it does not do

- It does **not** trade. The ML module returns predictions; you decide what to
  do with them.
- It does **not** guarantee accuracy. Walk-forward accuracy in the 50–60% range
  is the realistic ceiling for this feature set on daily bars. The UI shows
  this.
- It does **not** use intraday data. Yahoo provides only daily bars for most
  NSE tickers, and the historical depth we cache is 2 years.

## Where it lives in the codebase

- Backend code: `backend/app/modules/ml/`
- Backend dev notes: `backend/docs/ml/`
- Optional extras: `xgboost`, `lightgbm`, `catboost`, `torch`, `shap`,
  `transformers`
- Frontend API client: `frontend/lib/api/ml.ts`
- Frontend hook: `frontend/lib/hooks/use-ml.ts`
- Consumer: signals fusion (`signals.service.get_fusion` imports `predict`)

## Consumed by (frontend pages and other modules)

- [Stock terminal](../../pages/stock-terminal/overview.md) — the AI card. The ensemble
  prediction (UP / DOWN, confidence) and the LSTM next-day price estimate are shown
  side by side.
- Module: [Signals](../signals/overview.md) — fusion calls `ml.predict` for the 40%
  ML weight in the verdict.

## Related pages in this folder

- [How it works](how-it-works.md) — the ensemble pipeline, the LSTM training, the
  walk-forward check, the job registry, the capabilities flags.
- [Implementation](implementation.md) — file map, every function, every constant,
  the schema, the request trace, gotchas.