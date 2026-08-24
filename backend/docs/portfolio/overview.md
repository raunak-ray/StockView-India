# Portfolio — Overview & Endpoints

**Plain words:** two features in one module — the **watchlist** (star a stock
and it shows on your dashboard) and **paper trading** (a ₹1,00,000 practice
game where you buy/sell at live prices with fake money).

## Watchlist endpoints

| Method & path | What it does |
|---|---|
| `GET /api/v1/portfolio/watchlist` | List your starred tickers |
| `POST /api/v1/portfolio/watchlist` | Add `{"ticker": "RELIANCE.NS"}` |
| `DELETE /api/v1/portfolio/watchlist/{ticker}` | Remove one |

All require login (401 otherwise). Adding a duplicate is safe — no double rows.

## Paper trading endpoints

| Method & path | What it does |
|---|---|
| `GET /api/v1/portfolio/paper` | Summary: cash, positions, orders, P&L |
| `POST /api/v1/portfolio/paper/order` | Place order — `{"symbol", "side", "qty", "price"}` |
| `GET /api/v1/portfolio/paper/positions` | Open positions with live P&L |
| `GET /api/v1/portfolio/paper/orders` | Order history (newest first) |
| `POST /api/v1/portfolio/paper/reset` | Reset to ₹1,00,000 |

Paper trading starts with ₹1,00,000 cash. Orders fill instantly at the
price you enter. State is per-user, in-memory — resets on server restart
(parity with the original Streamlit prototype).

Broker connectors (Kite, Upstox, Binance, Angel One) are flagged as
future work — not integrated yet.

## Where the code lives

`backend/app/modules/portfolio/`. Tests: `tests/test_portfolio.py` (watchlist),
`tests/test_paper.py` (paper trading).
