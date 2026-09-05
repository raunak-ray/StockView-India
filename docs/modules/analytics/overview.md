# Analytics — what it is

The analytics module computes **technical indicators** over price history — the
trend averages, momentum oscillators, and volatility bands that traders draw on
charts and feed into signal rules.

It is a pure-maths module: take price candles in, return indicator series out. It
does not make predictions or generate buy/sell verdicts — that is what the signals
module does on top.

## What you can do with it

- **Fetch indicator series** for a symbol: SMA-20, SMA-50, EMA-20, Bollinger
  upper/mid/lower, RSI, ATR, MACD, MACD signal, MACD histogram.
- **Fetch support and resistance levels** — the prices the stock has historically
  bounced off, plus which one is nearest below/above the current close.

The first is what the chart overlays draw. The second is what the "key levels"
panel shows under the chart.

## Indicators in plain English

Each indicator answers one question:

| Indicator | Question | Used for |
|---|---|---|
| SMA-20 / SMA-50 | Average price over the last N days. Smooths out the noise. | Trend line on chart, golden/death cross |
| EMA-20 | Like SMA but weights recent days more. | Faster trend line |
| Bollinger Bands (BB_H / BB_M / BB_L) | Price range based on recent volatility. | Breakouts, "price is stretched" calls |
| RSI | 0–100 score: is momentum overbought (>70) or oversold (<30)? | Signal rules |
| ATR | Average True Range — typical daily price swing. | Volatility sizing, stop-loss distance |
| MACD + signal + histogram | Difference between two moving averages, plus a signal line. | Crossover detection, momentum |

The module computes all of them from one set of candles. The frontend decides
which ones to draw.

## A real example

You open SBIN. The chart loads, then the analytics endpoint returns:

- `sma20`: 502 points (about 2 years daily), one per day, NaN for the first 19.
- `rsi`: 502 points; latest value `68.3` (close to overbought but not there).
- `bb_high` / `bb_low`: the volatility envelope for the last 20 days.

The chart overlays SMA-20 and SMA-50 as two lines. The signal panel reads RSI
and MACD to decide SBIN's verdict. The key-levels panel shows the support level
near ₹780 (where SBIN bounced twice in the last 6 months) and the resistance
near ₹830 (where it failed to break in August).

## Why a separate module

- **One place for indicator math.** Every indicator calculation lives here. The
  signals module imports `add_indicators` from here and runs rules on top.
- **No external dependencies beyond pandas + ta.** All indicators are computed
  locally. No remote indicator service.
- **Indicator changes happen here.** If you want to add a new indicator (say,
  Keltner Channels or VWAP), you add one column to `add_indicators`, one entry
  in `_COLUMN_MAP`, and one entry in `IndicatorsResponse`.

## Where it lives in the codebase

- Backend code: `backend/app/modules/analytics/`
- Backend dev notes: `backend/docs/analytics/`
- Indicator library: `ta` (https://github.com/bukosabino/ta)
- Data source: `backend/app/modules/market_data/` (candles via Redis cache)
- Consumer: `backend/app/modules/signals/service.py` (calls `add_indicators`)
- Frontend API client: `frontend/lib/api/analytics.ts`
- Frontend hook: `frontend/lib/hooks/use-analytics.ts`
- Chart consumers: stock-terminal page, signals panel

## Consumed by (frontend pages and other modules)

- [Stock terminal](../../pages/stock-terminal/overview.md) — main chart + indicator sub-charts.
- [Backtest](../../pages/backtest/overview.md) — computes indicators on historical candles for
  the strategy backtest (e.g. SMA cross uses the 20/50 SMA, RSI uses the 14-period RSI).
- Module: [Signals](../signals/overview.md) — calls `add_indicators` to enrich the candle
  DataFrame before running the 10-rule engine.
- Module: [SMC](../smc/overview.md) — uses `candles_to_df` to construct the price series
  for pivot detection and structure analysis.

## Related pages in this folder

- [How it works](how-it-works.md) — the candle → DataFrame → indicator series flow,
  support/resistance algorithm, threadpool usage.
- [Implementation](implementation.md) — file map, the indicator table, the S/R
  cluster algorithm, frontend wiring.