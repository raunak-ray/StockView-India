# Dashboard — what it is

The dashboard is the **home screen at `/app`** — the first page a logged-in
user sees after login. It is the bird's-eye view of the market plus the
user's personal view of their watchlist.

The page is intentionally light. It does three things:

1. **Greet you** by name and time of day.
2. **Show the market** at a glance: 5 NSE indices + top 5 gainers + top 5 losers.
3. **Show your watchlist** with live prices and the ability to remove items.

Anything more — full charts, individual stock pages, news, signals — lives
on a dedicated page (e.g. `/app/stocks/RELIANCE.NS` for the stock terminal).

## What visitors see

Reading top to bottom:

| Section | What it is |
|---|---|
| **Greeting header** | "Good morning, demo" + today's date + a small market status chip (open/closed) |
| **Market snapshot** | 5 cards: NIFTY 50, SENSEX, BANK NIFTY, NIFTY IT, NIFTY AUTO — price + % change |
| **Market movers** | A side-by-side list: top 5 gainers on the left, top 5 losers on the right |
| **My watchlist** | The user's saved tickers with live prices and a remove button |

The page has no fixed time-of-day greeting (it changes with the user's local
time). The greeting is "Good morning", "Good afternoon", or "Good evening"
based on the hour.

## A real example

You log in as `demo` at 10:30 AM. You see:

- **Header**: "Good morning, demo · Mon, 17 Apr 2026 · Market open"
- **Market snapshot**: 5 cards. NIFTY 50 at 24,580 (+0.42%), SENSEX at 80,250
  (+0.51%), etc. Each card has a green or red arrow and a percentage.
- **Market movers**: 5 gainers (TATAMOTORS +3.4%, INFY +2.1%, …) and 5 losers
  (WIPRO −2.8%, TECHM −2.1%, …). Each row is a link to that stock's
  terminal.
- **My watchlist**: 3 starred tickers (RELIANCE.NS, TCS.NS, HDFCBANK.NS)
  with live prices refreshing every 60 seconds. The remove button (X) shows
  on hover.

You click a mover row → navigate to `/app/stocks/INFY.NS` (the stock
terminal). The dashboard does not have charts — that's the next page.

## Why the dashboard is small on purpose

- **It is a hub, not a destination.** The dashboard answers "what should I
  look at?". It does not try to be the workbench.
- **Load time matters.** Five index cards + 10 movers + the watchlist is
  the minimum a user needs to start their session. Adding more would slow
  the first paint.
- **The watchlist is the only personal data.** Everything else is market-wide
  and identical for every user.

## What the page does not do

- It does not show charts. Charts are on `/app/stocks/[symbol]`.
- It does not show news. News is on the stock terminal.
- It does not show portfolio / paper trading. That's `/app/paper-trading`.
- It does not show alerts. That's `/app/alerts`.
- It does not show settings. That's `/app/settings`.

## Where it lives in the codebase

- Page: `frontend/app/(app)/app/page.tsx` (the URL is `/app`)
- Greeting + layout: `frontend/app/(app)/app/page.tsx` (52 lines)
- App shell: `frontend/app/(app)/app/components/app-shell.tsx` (sidebar + topbar)
- Index cards: `frontend/app/(app)/app/components/index-cards.tsx`
- Movers: `frontend/app/(app)/app/components/movers-panel.tsx`
- Watchlist: `frontend/app/(app)/app/components/watchlist-card.tsx`

## Backend modules used

- [Market data](../../modules/market-data/overview.md) — index quotes (Nifty, Sensex,
  Bank Nifty) and movers.
- [NSE](../../modules/nse/overview.md) — `GET /quote` for the index cards (falls through
  to Yahoo if NSE is down).
- [Portfolio](../../modules/portfolio/overview.md) — `GET /watchlist` for the watchlist card.
- [Instruments](../../modules/instruments/overview.md) — sector list for the movers filter.
- [Auth](../../modules/auth/overview.md) — `GET /me` for the greeting.

## Related pages in this folder

- [How it works](how-it-works.md) — the greeting logic, the section flow,
  the data sources, the per-card refresh behaviour, the watchlist live
  prices.
- [Implementation](implementation.md) — file map, every hook, the `useQuote`
  poll, the watchlist remove flow, the route guard chain, the request
  traces.