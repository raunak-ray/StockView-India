# Paper trading — what it is

The Paper Trading page is the **simulated trading portfolio at
`/app/paper-trading`**. It is a virtual ₹1,00,000 (1 lakh) brokerage
account where you can place buy and sell orders, see open positions,
and track realised and unrealised P&L — all without touching real
money.

It is the "try it before you risk it" page. You can practice trading
strategies, learn the mechanics of position management, and see how
the numbers move when you buy or sell.

## What visitors see

A title "Paper Trading" with a small "Reset" button on the right.
Below, four summary stat cards. Below that, the order ticket. Below
that, a 2-tab strip showing Positions or Orders.

| Section | What it is |
|---|---|
| **Header** | Title + Reset button (returns the portfolio to ₹1,00,000) |
| **Summary cards** | Cash, Positions count, Orders count, Realised P&L |
| **Order ticket** | Symbol search + side (BUY/SELL) + qty + price + estimated cost + submit button |
| **Tabs** | Positions (open holdings with LTP and P&L) or Orders (chronological history) |

The page is a single column with a max width of 768px (`max-w-3xl`).
It is the second-narrowest page in the app (settings is the
narrowest).

## A real example

You start with ₹1,00,000 cash, 0 positions, 0 orders.

You place a BUY order for RELIANCE.NS — 10 shares at ₹2,945.00.
Estimated cost: ₹29,450. After the order:

- **Summary cards**: Cash ₹70,550, Positions 1, Orders 1, Realised P&L
  ₹0.
- **Positions tab**: RELIANCE.NS, 10 shares @ ₹2,945.00 avg cost, LTP
  ₹2,945.00, unrealised P&L ₹0 (0.00%). The P&L will move with the
  live price.
- **Orders tab**: BUY 10 × RELIANCE.NS @ ₹2,945.00, value ₹29,450.00.
  Order ID like `P-1700000000-1`.

You wait an hour. RELIANCE.NS moves to ₹2,975.00. The position's LTP
updates to ₹2,975.00. Unrealised P&L: +₹300.00 (+1.02%).

You SELL all 10 shares at ₹2,975.00. After the order:

- **Summary cards**: Cash ₹1,00,300, Positions 0, Orders 2, Realised
  P&L +₹300.
- **Positions tab**: "No open positions."
- **Orders tab**: Two orders — the original BUY and the SELL.

The Reset button restores the initial state. Cash back to ₹1,00,000,
positions and orders cleared.

## The order ticket

The order ticket is a card with five controls:

1. **Symbol** — A `SymbolSearch` input. Type to find any NSE stock.
2. **Side** — Two buttons: BUY (green) and SELL (red). Mutually
   exclusive.
3. **Quantity** — A number input, default 1, min 1.
4. **Price** — A number input for the order price. Required.
5. **Submit button** — Big, full-width, coloured by side (green for
   BUY, red for SELL). Label is "BUY (Paper)" or "SELL (Paper)".

Below the controls: estimated cost (qty × price) and current cash
balance.

### Quick-pick from watchlist

If the user has a watchlist, up to 4 watchlist tickers are shown as
small chips below the symbol search. Click a chip to set the symbol.
The currently-selected symbol's chip is highlighted.

## The position row

Each open position is a row with:

- The symbol (mono, bold).
- "N shares @ ₹X,XXX" (avg cost).
- "LTP ₹X,XXX" (last traded price).
- Unrealised P&L (in ₹ and %) — green if positive, red if negative.

The LTP is the **live quote** from the market-data module. The P&L is
`(LTP − avg_cost) × qty`.

## The order row

Each order is a row with:

- A side pill (BUY/SELL) — green for BUY, red for SELL.
- The symbol (mono, bold).
- "N × ₹X,XXX" (qty × price).
- The total value (qty × price).
- The order ID (small, mono, muted).

Orders are sorted newest-first (the most recent order at the top).

## The reset button

A small ghost button in the header. Click to reset the entire paper
portfolio to its initial state. This:

- Resets cash to ₹1,00,000.
- Clears all open positions.
- Clears the order history.

The reset is irreversible — there is no undo. The toast confirms
"Portfolio reset to ₹1,00,000".

## What the page does not do

- **It does not use real money.** Every order is a paper order. There
  is no broker integration.
- **It does not support order types.** Only market-equivalent orders
  (you specify the exact price; the backend immediately fills at that
  price).
- **It does not support short selling.** You can only SELL what you
  own. The backend rejects SELL orders that exceed your holding.
- **It does not support stop-loss or take-profit.** The price you
  enter is the fill price.
- **It does not persist across server restarts.** The paper portfolio
  is in-memory. A server restart wipes the data (with the seed: ₹1L
  cash, no positions, no orders).
- **It does not persist across devices.** Each user has their own
  paper portfolio (the key is the user ID).

## Where it lives in the codebase

- Page: `frontend/app/(app)/app/paper-trading/page.tsx` (396 lines, all
  components inline)
- API client: `frontend/lib/api/portfolio.ts` (paper methods)
- Hooks: `frontend/lib/hooks/use-paper.ts`
- Backend: [portfolio module](../../modules/portfolio/overview.md) —
  see "paper trading" section
- Components used:
  - `SymbolSearch` from `@/components/symbol-search`
  - `Tabs` from `@/components/ui/tabs`

## Backend modules used

- [Portfolio](../../modules/portfolio/overview.md) — the primary backend. The paper-trading
  endpoints (`GET /paper/portfolio`, `POST /paper/orders`, `DELETE /paper/orders`,
  `GET /paper/orders`, `POST /paper/reset`) all live here.
- [Market data](../../modules/market-data/overview.md) — `GET /quote` for the live
  price of open positions (refreshed every 30s).
- [Instruments](../../modules/instruments/overview.md) — symbol search in the order form.

## Related pages in this folder

- [How it works](how-it-works.md) — the form state, the order
  lifecycle, the summary stat cards, the positions table, the orders
  table, the reset flow.
- [Implementation](implementation.md) — file map, the LTP update
  flow, the cache invalidation, the request traces.