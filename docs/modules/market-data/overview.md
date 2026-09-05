# Market data — what it is

The market-data module fetches **live and historical prices** for Indian stocks and
indices from Yahoo Finance. It is the data source for almost everything else in
StockView — analytics, signals, charts, watchlist, paper trading, alerts all read
through this module.

Nothing in StockView talks to Yahoo directly. Every price, every candle, every index
quote passes through one of the six endpoints here.

## What you can do with it

- Pull **historical OHLCV candles** for a symbol (e.g. RELIANCE.NS, 2 years daily).
- Get a **live quote** — last price, change, percent change.
- Fetch **company info** — sector, market cap, P/E, description.
- See the **market summary** — Nifty 50, Sensex, Bank Nifty, IT, Gold.
- See the **sector performance heatmap** — average % change per NIFTY sector.
- See **top 5 gainers and losers** among NSE large-caps.

## Why it exists as a separate module

- **Single point of cache.** Every call goes through Redis. Yahoo Finance has rate
  limits; without cache, the dashboard alone would fire hundreds of calls per minute.
- **Single point of error handling.** Yahoo returns empty frames, NaN values,
  multi-index columns, missing fields. This module normalises all of that into one
  shape the rest of the app can rely on.
- **Single point of retries/fallbacks.** Quote falls back from `fast_info` to
  intraday history if needed. Market summary tries daily bars, then minute bars,
  then per-ticker `fast_info`. All of that lives here.

## A real example

You open RELIANCE. The terminal calls `/api/v1/market/history?symbol=RELIANCE.NS&interval=1d&period=2y`.
The server checks Redis for `md:history:RELIANCE.NS:1d:2y`.

- If cached (within 5 minutes): returns immediately.
- If not: asks Yahoo, gets ~500 daily candles, drops NaN rows, serialises to JSON,
  stores in Redis with 300-second TTL, returns to the client.

The next page load within 5 minutes gets the cached version. No Yahoo call.

## Symbols you can query

| What | Format | Example |
|---|---|---|
| NSE equity | `TICKER.NS` | `RELIANCE.NS`, `TCS.NS`, `INFY.NS` |
| BSE equity | `TICKER.BO` | `RELIANCE.BO` |
| NSE index | `^NSEI` etc. | `^NSEI` (Nifty 50), `^BSESN` (Sensex) |
| Commodity | `GC=F` | `GC=F` (Gold) |

The instruments module (`docs/modules/instruments/`) provides a curated map from
human-readable names ("Reliance Industries") to these Yahoo tickers.

## Where it lives in the codebase

- Backend code: `backend/app/modules/market_data/`
- Backend dev notes: `backend/docs/market_data/`
- Cache helper: `backend/app/core/cache.py` (Redis)
- Frontend API client: `frontend/lib/api/market.ts`
- Frontend hook: `frontend/lib/hooks/use-market.ts`
- Frontend consumers: stock-terminal, dashboard, markets, sectors pages

## Consumed by (frontend pages)

This is the most-consumed module on the backend — almost every page hits it.

- [Stock terminal](../../pages/stock-terminal/overview.md) — quote, history, info.
- [Dashboard](../../pages/dashboard/overview.md) — index cards, movers, watchlist quotes.
- [Markets](../../pages/markets/overview.md) — NSE quote tab falls through to Yahoo.
- [Sectors](../../pages/sectors/overview.md) — sector & stock prices for the treemap.
- [Compare](../../pages/compare/overview.md) — history for 2–4 symbols.
- [Backtest](../../pages/backtest/overview.md) — historical OHLCV.
- [Paper trading](../../pages/paper-trading/overview.md) — last price for position P&L.
- [Alerts](../../pages/alerts/overview.md) — live quote for the threshold check.

## Related pages in this folder

- [How it works](how-it-works.md) — caching, the fallback chain, threadpool usage,
  multi-index columns handling.
- [Implementation](implementation.md) — file map, endpoint table, every helper, the
  sector algorithm, frontend wiring.