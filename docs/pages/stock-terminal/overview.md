# Stock terminal — what it is

The stock terminal is the **detail page for a single stock** at
`/app/stocks/[symbol]`. It is the most data-dense page in the app. Every
backend module eventually shows up here — chart, indicators, signals, SMC
zones, ML prediction, news, sentiment, verdict.

It is the "deep dive" page. The dashboard is the bird's-eye view; this is
the per-symbol workspace.

The URL takes the ticker symbol. Examples:

- `/app/stocks/RELIANCE.NS` — Reliance Industries on NSE.
- `/app/stocks/TCS.BO` — TCS on BSE.
- `/app/stocks/^NSEI` — NIFTY 50 index.
- `/app/stocks/UNKNOWN` — a symbol the backend does not recognise, which
  renders a "we couldn't find" empty state.

## What visitors see

Reading top to bottom:

| Section | What it is |
|---|---|
| **Back link** | A small "← Dashboard" link to go back |
| **Header** | Company name, ticker, exchange badge (NSE / BSE / INDEX), market status chip, big price, change %, refresh interval picker, watchlist star |
| **Chart** | The full TradingView-style candlestick or line chart with overlays (SMA, BB, RSI, MACD, S/R, signals, SMC zones) |
| **Today stats** | Open, prev close, day high/low, volume, avg volume |
| **52-week range** | Low/high, current position bar, market cap |
| **Fusion verdict** | A 320-wide card with the 3-layer blend (technical + ML + news) + confidence tier + active rules + reasons |
| **News & mood** | News headlines with tone badges, news mood meter, chart mood meter |
| **AI prediction** | Next 5 days ensemble verdict, model accuracies, LSTM forecast, top features |

The page is ~3000px tall on a desktop. On mobile, sections stack vertically
and the verdict/AI cards reflow.

## A real example

You click the RELIANCE.NS mover on the dashboard. The stock terminal loads:

- **Header**: "Reliance Industries" + `RELIANCE.NS` + `NSE` badge + market
  status. Price ₹2,945.30, +0.42% (green up arrow). The refresh interval
  picker shows "10s" highlighted (default).
- **Chart**: A candlestick chart with SMA 20 (gold) and SMA 50 (info blue)
  lines. The current price line is visible. Volume bars at the bottom.
  S/R dashed lines if supports/resistances are present. Buy/sell markers
  along the price line. RSI panel below the main chart.
- **Today stats**: Open ₹2,940.10, Prev close ₹2,932.80, Day high ₹2,968.50,
  Day low ₹2,921.00, Volume 8.5M, Avg vol (10D) 7.2M.
- **52-week range**: Low ₹2,220.10, High ₹3,024.50, current position
  indicator (around 70% along the gradient bar). Market cap ₹19.9T.
- **Fusion verdict**: "BUY" badge with a +0.32 fused score. Three
  horizontal bars showing the 45/40/15 split. Confidence: HIGH. Top
  rules: "RSI oversold bounce", "MACD bullish cross", "Volume surge".
- **News & mood**: News mood: POSITIVE (+0.18), Chart mood: BULLISH (+0.42).
  Top 3 chart signals: "RSI > 50", "MACD > signal", "Price above SMA-20".
  8 headlines listed with tone badges.
- **AI prediction**: "UP" verdict with 62% confidence. Walk-forward 56.8%.
  Model accuracies: XGBoost 58.2, LightGBM 56.4, CatBoost 57.1. LSTM
  tomorrow's price: ₹2,978.20 (+1.12%). Top 3 features: rsi_14, macd_diff,
  volume_change.

## What the page does

- **Streams live quotes.** The header price auto-refreshes every 10s
  (default; can be 5/10/15/30/60s).
- **Re-fetches chart data on timeframe change.** Clicking "1W" re-fetches
  5 years of weekly data.
- **Fuses 3 layers of signal** (technical + ML + news) into a single
  verdict.
- **Renders SMC zones** (order blocks, fair value gaps, premium/discount
  zones) when the SMC toggle is on.
- **Computes ML predictions** (ensemble + LSTM) per symbol.
- **Shows live news headlines** with FinBERT or keyword sentiment scores.

## What the page does not do

- **Trading.** It is research-only. Buy/sell buttons would take you to a
  broker, which is out of scope.
- **Watchlist editing inline.** The star button adds/removes the ticker
  from your watchlist, but the dashboard is the place to manage the full
  list.
- **Alert creation.** That's the alerts page. The page does not let you
  set a price alert from here (you have to navigate to `/app/alerts`).
- **Backtesting.** That's a separate page. The chart is historical only.
- **Comparison.** That's `/app/compare`. This page is one symbol.

## The timeframes

Three chart timeframes:

| Label | Interval | Period |
|---|---|---|
| 1D | 1d (daily) | 2 years |
| 1W | 1wk (weekly) | 5 years |
| 1M | 1mo (monthly) | 10 years |

The 1D/1W/1M labels are user-facing. The backend's `interval` and `period`
are passed through to yfinance. Switching to 1W re-fetches 5 years of
weekly bars.

The default is 1D. Persisted only for the current page session — refresh
returns to 1D.

## The refresh intervals

Five options for the live-quote poll: 5s, 10s, 15s, 30s, 60s. Default 10s.
The chart is **not** re-fetched on each interval — only the price quote in
the header.

## Why this page is heavy

- **Many endpoints.** Six in parallel: quote, history, info, indicators,
  S/R, signal, SMC, fusion, sentiment, ML predict, LSTM.
- **Large data.** 2 years of daily bars = ~500 candles. Each candle has
  OHLCV.
- **Heavy compute on the backend.** Indicators, signal fusion, ML
  prediction — all of it runs on each page load (cached for 30s+).
- **Multiple overlays.** The chart can show 5+ overlay types
  simultaneously (SMA × 2, BB, S/R, signals, SMC).

## Where it lives in the codebase

- Page: `frontend/app/(app)/app/stocks/[symbol]/page.tsx` (8 lines)
- Constants: `frontend/app/(app)/app/stocks/[symbol]/constants.ts`
- Hooks: `frontend/app/(app)/app/stocks/[symbol]/hooks/use-document-title.ts`
- Components:
  - `components/quote-view.tsx` — the page composition
  - `components/chart-section.tsx` — the chart and overlay toggles
  - `components/verdict-card.tsx` — the 3-layer fusion card
  - `components/news-card.tsx` — news + mood
  - `components/ai-card.tsx` — ML ensemble + LSTM
  - `components/watchlist-star.tsx` — the star button

## Backend modules used

The most module-consuming page on the frontend. It calls 11 endpoints
across 9 modules in parallel.

- [Market data](../../modules/market-data/overview.md) — `GET /quote`, `GET /history`,
  `GET /info` (cached).
- [Analytics](../../modules/analytics/overview.md) — `GET /indicators` (RSI, MACD, BB, ATR, SMA, EMA).
- [Signals](../../modules/signals/overview.md) — `GET /fusion` (the 3-layer verdict).
- [SMC](../../modules/smc/overview.md) — `GET /smc` (BOS, CHoCH, OB, FVG overlay).
- [Sentiment](../../modules/sentiment/overview.md) — `GET /headlines` + `GET /score`.
- [ML](../../modules/ml/overview.md) — `GET /predict` (ensemble) and `GET /predict/lstm`.
- [NSE](../../modules/nse/overview.md) — `GET /quote` as a fallback when Yahoo is down.
- [Portfolio](../../modules/portfolio/overview.md) — `GET /watchlist` + `POST /watchlist` (the star button).
- [Auth](../../modules/auth/overview.md) — `GET /me` (for the topbar avatar).

## Related pages in this folder

- [How it works](how-it-works.md) — the page composition, the data flow
  per section, the chart overlay toggles, the verdict math, the AI card
  states.
- [Implementation](implementation.md) — file map, every hook, the
  constants, the verdict math, the chart payload, the request traces.