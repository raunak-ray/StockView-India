# Dashboard — Overview

**Plain words:** your home screen after logging in — the market at a glance.

## What's on it

- **Market status chip** (top bar) — green while NSE is open (IST market
  hours), grey when closed.
- **Index cards** — NIFTY 50, SENSEX, BANK NIFTY… refreshing every 60s.
- **Gainers / Losers panel** — the day's biggest movers; click a row to open
  that stock's page.
- **Watchlist panel** — your starred stocks with live per-row prices and
  one-click remove (updates instantly, then syncs).

## Good to know

- ⌘K / Ctrl-K command palette works everywhere: type a stock name, Enter,
  land on its page.
- Panels load independently: one failing panel shows a short error note
  while the rest keep working.

## Where the code lives

`frontend/app/(app)/app/` — `page.tsx` + `components/` (index-cards,
movers-panel, watchlist-card, app-shell). Hooks: `lib/hooks/use-market.ts`,
`lib/hooks/use-watchlist.ts`.

## Coming later

Paper-trading summary card and an alerts bell (Phases 7–8 of the plan).
