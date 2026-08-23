# Signals — Decision Pipeline

## From candles to verdict

```mermaid
flowchart LR
    H[Price history<br/>cached candles] --> I[Indicators<br/>RSI · MACD · SMA · ATR]
    I --> R{Rule checks}
    R -->|price above SMA50| V1[+bullish vote]
    R -->|RSI > 70| V2[-overbought vote]
    R -->|MACD cross| V3[+/- momentum vote]
    R -->|volume confirms| V4[+strength vote]
    V1 & V2 & V3 & V4 --> S[Score −15…+15]
    S --> VERDICT{{BUY / HOLD / SELL<br/>+ confidence}}
    VERDICT --> WHY["Why" card on the stock page]
```

## Reading the result

- Score near **+15**: many rules agree upward → BUY.
- Score near **−15**: the reverse → SELL.
- Rules disagree → HOLD with lower confidence.

The stop-loss suggestion comes from ATR: "leave the trade if price falls
roughly one average daily move below entry."
