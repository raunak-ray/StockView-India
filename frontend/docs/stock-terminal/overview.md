# Stock Terminal — Overview

**Plain words:** the heart of the app — the full page for one stock, e.g.
`/app/stocks/RELIANCE.NS`.

## What's on it

- **Live quote header** — price, day change, open/high/low, 52-week range
  bar; auto-refresh you choose (5s → 60s, or off).
- **The chart** — candles or line, volume below, overlays (SMA 20/50,
  Bollinger), RSI + MACD panes, support/resistance lines, buy/sell markers,
  and optional SMC zones. Time presets 1D / 1W / 1M. See
  [chart-layers.md](chart-layers.md).
- **Verdict card** — BUY / HOLD / SELL badge, score gauge (−15…+15),
  confidence, rule chips, plain "Why" list.
- **News & mood card** — headlines with tone badges plus two mood meters
  (news tone, chart indicators), each −1…+1.
- **AI prediction card** — ensemble verdict with probability gauge, 1/3/5-day
  horizons, per-model accuracies, top features and the LSTM tomorrow-price
  forecast. Tooltips explain every concept.
- **Star button** — add/remove from your watchlist.

## Good to know

Built on `lightweight-charts` (TradingView's open-source library) — fast
pan/zoom. Chart, verdict and levels share one cached copy of the candles.

## Where the code lives

`frontend/app/(app)/app/stocks/[symbol]/` — page + components beside it.
Shared renderer: `components/charts/price-chart.tsx`.

## Coming later

Fusion verdict, analysis matrix.
