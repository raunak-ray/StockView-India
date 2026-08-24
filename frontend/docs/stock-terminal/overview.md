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
- **Fusion verdict card** — STRONG BUY / BUY / NEUTRAL / SELL / STRONG SELL
  badge, fused score gauge, 3-layer blend bars (technical 45%, ML 40%,
  news 15%), confidence tier badge, "what's missing" hints, rule chips,
  and the plain "Why" list. Tooltips on every concept.
- **News & mood card** — headlines with tone badges plus two mood meters
  (news tone, chart indicators), each −1…+1.
- **AI prediction card** — ensemble verdict with probability gauge, 1/3/5-day
  horizons, per-model accuracies, top features and the LSTM tomorrow-price
  forecast.
- **Star button** — add/remove from your watchlist.

## Where the code lives

`frontend/app/(app)/app/stocks/[symbol]/` — page + components beside it.
Shared renderer: `components/charts/price-chart.tsx`.
