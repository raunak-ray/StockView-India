# Compare — what it is

The Compare page is the **side-by-side comparison at `/app/compare`**. It
lets you pick 2 to 4 NSE stocks and see their key metrics, prices, and
normalised performance on one screen.

The trick is the **price normalisation**: every stock is rebased to 100
on the first common trading day, so a ₹3,000 stock and a ₹400 stock share
the same chart axis fairly.

It is the lightest of the "deep-dive" pages — no chart with overlays, no
signals, no AI. Just snapshot cards, a normalised chart, and a comparison
table.

## What visitors see

A title "Compare" with a subtitle "Pick 2–4 stocks to see them side by
side." A grid of 2 slot cards (the minimum). When you add a stock, the
empty slot becomes a snapshot card.

Reading top to bottom on a typical visit:

| Section | What it is |
|---|---|
| **Header** | Title + period dropdown (when at least 1 stock is selected) + "Clear all" button |
| **Slot cards** | 2–4 cards: snapshot cards (filled) or empty slots (with a plus icon) |
| **Add-stock card** | When 2–3 stocks are picked: a "+" card to add another (capped at 4) |
| **Normalised chart** | A line chart with each stock's rebased performance |
| **Side-by-side table** | 11 metrics × N stocks, aligned in a single table |

The colour of each card matches the colour of the corresponding line in
the chart (green, red, blue, yellow). This makes it easy to read
across the cards and the chart.

## A real example

You pick RELIANCE.NS, TCS.NS, INFY.NS, and HDFCBANK.NS over 1 year.

- **Cards** (left-to-right):
  - RELIANCE — green: ₹2,945.30, +0.42% today. 1y return: +12%.
  - TCS — red: ₹3,920.50, −0.18% today. 1y return: +5%.
  - INFY — blue: ₹1,485.60, +1.20% today. 1y return: +8%.
  - HDFCBANK — yellow: ₹1,672.40, +0.65% today. 1y return: +15%.
- **Normalised chart**: 4 lines starting at 100, diverging. HDFCBANK at
  the top (115), RELIANCE next (112), INFY in the middle (108), TCS at
  the bottom (105).
- **Comparison table**:

  | Metric | RELIANCE | TCS | INFY | HDFCBANK |
  |---|---|---|---|---|
  | Price | ₹2,945.30 | ₹3,920.50 | ₹1,485.60 | ₹1,672.40 |
  | Change | +0.42% | −0.18% | +1.20% | +0.65% |
  | Volume | 8.5M | 2.1M | 6.2M | 9.8M |
  | Market Cap | ₹19.9T | ₹14.2T | ₹6.2T | ₹12.7T |
  | P/E | 25.4 | 28.1 | 24.8 | 19.2 |
  | RSI | 62 | 48 | 71 | 55 |
  | 52W High | ₹3,024 | ₹4,100 | ₹1,520 | ₹1,720 |
  | 52W Low | ₹2,220 | ₹3,300 | ₹1,180 | ₹1,420 |
  | SMA 20 | ₹2,890 | ₹3,950 | ₹1,460 | ₹1,650 |
  | SMA 50 | ₹2,820 | ₹3,980 | ₹1,420 | ₹1,610 |
  | MACD | +12.45 | −2.10 | +5.80 | +8.20 |

You change the period to "3y". The cards re-fetch (with a brief loading
state), the chart redraws, the table updates. The stock colours stay the
same.

## The slot UX

The page has a 2-column slot grid. On a fresh visit (no symbols), both
slots are empty "+" placeholders. Click one → a stock picker modal
opens. Pick a stock → the slot becomes a snapshot card.

The slot is **always 2 columns wide** on `sm` and up, regardless of how
many stocks you have. With 1 stock, the second slot is an empty
placeholder (or an "Add another" card if the first slot is filled).

With 4 stocks, the slot grid is full and no "Add" card is shown.

## The stock picker

The picker is a modal (not inline). It uses the `instruments` search to
find any NSE stock. Already-picked stocks are excluded from the search
results. The modal supports a click-to-pick workflow:

1. Search for a stock (e.g. "infy").
2. Click a result.
3. The modal closes. The slot fills with the snapshot.

The picker is shared with other pages — `StockPickerModal` from
`@/components/stock-picker-modal`.

## What the page does not do

- It does not let you compare across exchanges (BSE vs NSE).
- It does not show intraday data. Just daily, weekly, or monthly
  depending on the period.
- It does not show signals, SMC zones, or AI verdicts. The compare
  page is metrics-only.
- It does not persist the selection. Refresh and your slots are empty.
- It does not let you compare more than 4 stocks. The cap is to keep
  the chart legible.

## Where it lives in the codebase

- Page: `frontend/app/(app)/app/compare/page.tsx` (800 lines, all
  components inline)
- API client: `frontend/lib/api/compare.ts`
- Hook: `frontend/lib/hooks/use-compare.ts`
- Backend: [compare module](../../modules/compare/overview.md)
- Components used:
  - `StockPickerModal` from `@/components/stock-picker-modal`
  - `Select` from `@/components/ui/select`

## Backend modules used

- [Compare](../../modules/compare/overview.md) — the primary backend. `POST /compare` takes
  2–4 symbols and returns snapshot cards + a normalised chart series.
- [Market data](../../modules/market-data/overview.md) — `GET /history` for the chart
  (the compare module calls this internally).
- [Instruments](../../modules/instruments/overview.md) — symbol search in the picker modal.

## Related pages in this folder

- [How it works](how-it-works.md) — the slot state machine, the
  picker flow, the snapshot card, the normalisation chart, the
  comparison table.
- [Implementation](implementation.md) — file map, every component,
  the colour cycle, the slot add/edit/remove flow, the request
  traces.