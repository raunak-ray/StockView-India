# Portfolio — what it is

The portfolio module is **two features in one**:

- **Watchlist** — your starred stocks, persisted in the database.
- **Paper trading** — a simulated ₹1,00,000 portfolio for trying out trades
  without risking real money.

These are unrelated except for living in the same folder. The watchlist uses
SQLAlchemy + the real DB. Paper trading uses an in-memory dict per user.

## Watchlist

The watchlist is a simple list of Yahoo tickers per user. There is no
metadata — just the symbol. The UI usually pairs each row with live quotes
from `market_data`.

### What you can do

- `GET /portfolio/watchlist` — list your starred tickers.
- `POST /portfolio/watchlist` — add a ticker.
- `DELETE /portfolio/watchlist/{ticker}` — remove a ticker.

Duplicates (`user_id`, `ticker`) are rejected with `409`. The DB enforces
uniqueness via a `UniqueConstraint`, so even concurrent inserts cannot create
duplicates.

### Storage

A real SQLAlchemy table:

```python
class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_watchlist_user_ticker"),)
    id: Mapped[str]            # UUID
    user_id: Mapped[str]       # FK → users.id, ON DELETE CASCADE
    ticker: Mapped[str]        # e.g. "RELIANCE.NS"
    sort_order: Mapped[int]    # next-order = max + 1
    created_at: Mapped[datetime]
```

The `sort_order` column is for the drag-to-reorder UI feature. New items
default to `max(sort_order) + 1`, so the list is stable across inserts.

## Paper trading

The paper portfolio is a simulated broker account. You start with **₹1,00,000**
cash. Every order fills **instantly at the price you enter**. There is no
spread, no slippage, no partial fill.

### What you can do

- `GET /portfolio/paper` — summary: cash, position count, order count, realised P&L.
- `POST /portfolio/paper/order` — place a BUY or SELL.
- `GET /portfolio/paper/positions` — open positions with live P&L.
- `GET /portfolio/paper/orders` — order history (newest first).
- `POST /portfolio/paper/reset` — restore starting cash.

### The order model

```python
order = {
    "id": uuid.uuid4()[:8].upper(),  # 8-char id
    "ts": datetime.now(UTC).isoformat(),
    "symbol": "RELIANCE.NS",
    "type": "BUY" | "SELL",
    "qty": int,
    "price": float,        # fill price (instant)
    "value": round(qty * price, 2),
    "mode": "PAPER",
}
```

A `PaperOrder` is created in-memory only — no DB row. The order id is the first
8 chars of a UUID4 hex, uppercased (e.g. `"A3F7B29C"`).

### The position model

```python
position = {
    "symbol": "RELIANCE.NS",
    "qty": 10,
    "avg": 2950.0,   # weighted average cost
}
```

Average cost is a running weighted average. Buying 10 @ ₹2,950 then 5 @ ₹3,000
gives `qty=15, avg=(10*2950 + 5*3000) / 15 = 2966.67`. Selling reduces qty
without changing the average.

### A real example

You start with ₹1,00,000 cash, no positions.

| Order | Cash after | Position | Notes |
|---|---|---|---|
| BUY 10 RELIANCE @ 2950 | 70,500 | RELIANCE qty=10 avg=2950 | |
| BUY 5 RELIANCE @ 3000 | 55,500 | RELIANCE qty=15 avg=2966.67 | weighted average |
| Price moves to 3,050 | 55,500 | unrealised +₹1,250 (+2.8%) | shown in /positions |
| SELL 5 RELIANCE @ 3,050 | 70,750 | RELIANCE qty=10 avg=2966.67 | realised P&L: +₹416.65 |
| SELL 5 RELIANCE @ 2,900 | 85,250 | RELIANCE qty=5 avg=2966.67 | realised P&L: -₹333.35 |

The realised P&L `pnl` in the summary is the sum of closed trades. The
unrealised P&L per position is calculated from the live LTP minus average
cost.

### What it does not do

- **No broker connection.** Paper only. Kite / Upstox / Angel One integration
  is future work.
- **No persistence.** Restart the backend and the paper portfolio is gone.
  This is a known limitation. The watchlist (DB-backed) survives; the paper
  portfolio (in-memory) does not.
- **No margin / leverage.** You cannot buy on margin. If cash < cost, the
  order is rejected with `400`.
- **No shorting.** SELL requires existing qty. Selling more than you own is
  rejected with `400`.
- **No fees or taxes.** Real brokerages charge STT, GST, stamp duty. The
  paper portfolio is clean.

## Why a separate module

- **Watchlist and paper are conceptually different.** Watchlist is DB-backed,
  paper is in-memory. They share the same router for URL cohesion.
- **No signal interaction.** The paper portfolio does not read the signals
  or ML modules. You place orders manually.

## Where it lives in the codebase

- Backend code: `backend/app/modules/portfolio/`
  - `service.py` — watchlist (DB) operations
  - `paper_service.py` — paper trading (in-memory) operations
  - `models.py` — `WatchlistItem` SQLAlchemy model
- Backend dev notes: `backend/docs/portfolio/`
- Frontend API client: `frontend/lib/api/portfolio.ts`
- Frontend hook: `frontend/lib/hooks/use-paper.ts` (paper only)
- Frontend consumers: dashboard, paper-trading page, watchlist components

## Consumed by (frontend pages and other modules)

- [Dashboard](../../pages/dashboard/overview.md) — the watchlist card on the home
  screen reads the watchlist.
- [Paper trading](../../pages/paper-trading/overview.md) — the full page. Buy/sell
  ticket, open positions, order history.
- [Stock terminal](../../pages/stock-terminal/overview.md) — the watchlist star in
  the verdict card. Toggling it adds/removes a `WatchlistItem`.

## Known issues

- **Paper trading is in-memory** — a server restart wipes the cash balance and all
  positions. The PostgreSQL migration is in `plan/todo.md` Phase A.

## Related pages in this folder

- [How it works](how-it-works.md) — the watchlist CRUD, the order state
  machine, the average-cost update, the position enrichment.
- [Implementation](implementation.md) — file map, schemas, the in-memory
  state shape, request trace, gotchas.