# Stock Terminal — Overview

**Plain words:** the heart of the app — the full page for one stock, e.g.
`/app/stocks/RELIANCE.NS`. Everything about that stock on one screen.

## What's on it

- **Live quote header** — price, day change, open/high/low, 52-week range
  bar; auto-refresh you choose (5s → 60s, or off).
- **The chart** — candles or line, volume below, overlays (SMA 20/50,
  Bollinger), RSI + MACD panes, support/resistance lines, buy/sell markers,
  and optional SMC zones. Time presets 1D / 1W / 1M. See
  [chart-layers.md](chart-layers.md).
- **Verdict card** — BUY / HOLD / SELL badge, score gauge (−15…+15),
  confidence, rule chips, plain "Why" list.
- **Star button** — add/remove from your watchlist.

## Good to know

Built on `lightweight-charts` (TradingView's open-source library) — fast
pan/zoom on mouse or touch. Chart, verdict and levels share one cached copy
of the candles, so they always agree.

## Where the code lives

`frontend/app/(app)/app/stocks/[symbol]/` — page + components (chart-section,
quote-view, verdict-card, watchlist-star). Shared renderer:
`components/charts/price-chart.tsx`.

## Coming later

News tab, AI model tab, fusion verdict, analysis matrix.
