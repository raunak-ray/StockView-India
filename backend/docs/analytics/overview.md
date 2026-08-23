# Analytics — Overview & Endpoints

**Plain words:** takes plain price history and computes the "math helpers"
traders read on charts: averages, momentum gauges, bands, and levels where
price historically bounces.

## Endpoints

| Method & path | What it does |
|---|---|
| `GET /api/v1/analytics/indicators?symbol=&interval=&period=` | All indicator series for the chart |
| `GET /api/v1/analytics/support-resistance?symbol=&interval=&period=` | Up to 3 levels each side |

## What gets computed

- **SMA / EMA 20 & 50** — trend direction, noise smoothed away
- **RSI** — 0–100 momentum: high = overheated, low = exhausted
- **MACD + signal + histogram** — trend and momentum crosses
- **Bollinger Bands** — a corridor: wide = wild stock, tight = calm
- **ATR** — average daily movement size (for stop distances)
- **Support / Resistance** — price levels where the stock turned before,
  found by scanning pivots

## Where the code lives

`backend/app/modules/analytics/`. Tests:
`backend/tests/test_analytics_signals.py`.

## Good to know

Math is ported **unchanged** from the old prototype, so numbers match it
exactly. Indicators run on the same cached candles the chart uses — lines
always line up.
