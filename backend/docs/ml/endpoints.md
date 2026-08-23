# ML — Endpoints

All require login.

| Method & path | What it does |
|---|---|
| `GET /api/v1/ml/capabilities` | Which model libraries are installed + who votes |
| `POST /api/v1/ml/predict?symbol=&use_lstm=false` | Start a training job → `job_id` (202) |
| `GET /api/v1/ml/predict/{job_id}` | Poll: `running` → `done`/`error` + full result |
| `GET /api/v1/ml/lstm-forecast?symbol=` | Tomorrow's predicted close (₹) |
| `GET /api/v1/ml/eval?symbol=` | Walk-forward accuracy view of the last run |

## Why a job?

Training takes seconds to a minute. POST returns immediately with a job id;
poll GET until `status: "done"`. Results are cached ~15 min, so repeated
views are instant.

## Result highlights

- `direction` / `up_prob` — the ensemble verdict and its probability
- `horizon` — same vote for 1/3/5-day horizons
- `model_accs` — each model's holdout accuracy
- `walk_fwd_acc` — honest accuracy on unseen periods
- `top_features` — what influenced the vote most
- `predicted_price` — ATR-scaled next-candle estimate

## Installing the heavy models

`pip install -e ".[ml-heavy]"` unlocks XGBoost/LightGBM/CatBoost/torch;
without them the RF+GBM+LR fallback runs automatically.
