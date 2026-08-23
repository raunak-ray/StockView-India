# Sectors — Overview

**Plain words:** a heat-map of the whole NIFTY 50 grouped by sector. Big
boxes = big companies; box color = how much that stock moved today (emerald
= up, red = down). One glance answers "which parts of the market are hot".

## What's on it

- **Treemap** — NIFTY 50 companies sized by market cap, colored by % change,
  grouped into sectors. Click a sector to select it.
- **Performance bars** — sectors ranked by today's % change (signed bars).
- **Constituents table** — the selected sector's stocks with a debounced
  search filter; every row links to that stock's terminal page.

## Good to know

One batched download over the NIFTY-50 list, averaged per sector, cached
5 minutes — the page is fast the second time.

## Where the code lives

`frontend/app/(app)/app/sectors/` — page +
`components/sector-treemap.tsx` (a squarified treemap drawn in SVG, no chart
library). Data: `GET /api/v1/market/sector-performance` via
`lib/api/market.ts`.
