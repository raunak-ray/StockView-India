# Market Data — Overview & Endpoints

**Plain words:** downloads stock prices from Yahoo Finance (free) and serves
them: chart candles, live quotes, company facts, dashboard index cards,
gainers/losers, and per-sector averages.

## Endpoints

| Method & path | What it does | Cache |
|---|---|---|
| `GET /api/v1/market/history?symbol=&interval=&period=` | Chart candles | 300s |
| `GET /api/v1/market/quote?symbol=` | Live quote | 30s |
| `GET /api/v1/market/info?symbol=` | Company info | 600s |
| `GET /api/v1/market/market-summary` | Index cards | 60s |
| `GET /api/v1/market/sector-performance` | Sector averages | 300s |
| `GET /api/v1/market/gainers-losers` | Top movers | 60s |

`symbol` looks like `RELIANCE.NS`.

## Where the code lives

`backend/app/modules/market_data/`. Tests: `backend/tests/test_market_data.py`.

## Good to know

- Yahoo hiccups → **502**; wait a minute and retry.
- Free data can be delayed ~15 minutes — normal.
- Sector performance powers the `/app/sectors` treemap (one batched download
  over the NIFTY-50 list, averaged per sector).
