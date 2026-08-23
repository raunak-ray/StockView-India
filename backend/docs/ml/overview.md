# ML — Overview

**Plain words:** the computer studies ~2 years of a stock's history, learns
patterns, and votes on whether the price will be **higher in 5 trading
days**. Several models vote together (an *ensemble*) so one model's mistake
doesn't dominate. A separate LSTM network predicts **tomorrow's price in ₹**.

```mermaid
flowchart LR
    H[2y daily candles] --> F[31 engineered features<br/>momentum · volatility · candle shape]
    F --> E1[XGBoost] & E2[LightGBM] & E3[CatBoost]
    E1 & E2 & E3 --> V[Weighted vote + news bias]
    V --> OUT[UP/DOWN · probability · horizons 1/3/5d]
    F --> W[Walk-forward check<br/>tested on unseen periods]
    C[60 daily closes] --> L[PyTorch LSTM]
    L --> P[Tomorrow's close ₹]
```

- **No peeking ahead:** data is split chronologically (80% past → train,
  20% future → test); never shuffled.
- **Honest scoring:** walk-forward accuracy tests the model on periods it
  never saw. ~50% ≈ coin flip.
- **Graceful degradation:** without the optional libraries the scikit-learn
  trio (RF+GBM+LR) still votes — the app never breaks.

Education only: these are estimates on historical prices, not guarantees.
