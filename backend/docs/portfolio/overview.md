# Portfolio — Overview & Endpoints

**Plain words:** the star button. Star a stock anywhere and it appears on
your dashboard watchlist with live prices; unstar to remove. Each user's
list is private and stored in the database — it survives restarts, unlike
the old prototype which forgot everything on refresh.

## Endpoints

| Method & path | What it does |
|---|---|
| `GET /api/v1/portfolio/watchlist` | List your starred tickers |
| `POST /api/v1/portfolio/watchlist` | Add `{"ticker": "RELIANCE.NS"}` |
| `DELETE /api/v1/portfolio/watchlist/{ticker}` | Remove one |

All require login (401 otherwise). Adding a duplicate is safe — no double rows.

## Where the code lives

`backend/app/modules/portfolio/`. Tests: `backend/tests/test_portfolio.py`.

## What's coming to this module

Paper trading (the ₹1,00,000 practice portfolio) and price alerts — same
neighbourhood of the codebase (Phase 7–8 of the plan).
