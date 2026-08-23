# ML — The Two LSTMs

The project has two different "LSTM" models — easy to mix up.

## 1. Direction LSTM (inside the ensemble)

- **Question:** will price close higher in 5 days? (classification)
- **Reads:** 20 days × 13 engineered features (RSI zone, MACD distance,
  momentum, volatility…).
- **Architecture:** Bi-directional 2-layer LSTM (64 units) from the
  original prototype.
- Off by default (`use_lstm=false`) — it's the slowest voter.

## 2. Price LSTM (separate endpoint)

- **Question:** what is tomorrow's closing price in ₹? (regression)
- **Reads:** the last **60 daily closes** only.
- **Architecture:** two stacked LSTM layers of 50 units — a PyTorch port of
  the reference script `plan/lstm.py` (which used Keras; we reuse the
  project's existing torch dependency instead of adding TensorFlow).
- Trained per symbol on demand, cached for a day, chronological split.

## Reality check

Single-series price LSTMs are **naive**: they see only prices, no news or
context. Their forecasts are one opinion among several on the page — that's
why every prediction ships with the "estimates, not guarantees" note.
