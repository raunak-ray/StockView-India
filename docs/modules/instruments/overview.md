# Instruments — what it is

The instruments module is the **searchable catalogue** of stocks and indices that
StockView knows about. Every search box in the app, the sidebar filter, and the
sector treemap read from this one source.

There is no database for instruments. The data is a checked-in JSON file shipped
with the package. That keeps search fast (no network, no DB) and lets the data
ship with the code (one place to update, version-controlled).

## What you can do with it

- **List every supported symbol** — used by the search palette, the sidebar, and
  autocomplete dropdowns.
- **Search by name or ticker** — substring, case-insensitive, fast.
- **Get NIFTY 50 sector groupings** — used by the sectors heatmap to compute
  per-sector averages.

## Why a JSON file, not a database

- **Search is offline.** A regex match over ~300 strings is microseconds. No need
  for a DB.
- **The data is small and changes rarely.** A new IPO happens once a quarter.
  Index rebalancing is twice a year.
- **It travels with the code.** `git blame` on the JSON file tells you exactly when
  RELIANCE was added or when NIFTYIT was renamed. That history is impossible with
  a DB row.
- **It is loadable from package data.** `importlib.resources` reads it from the
  installed wheel, so the same code works in dev and in the Docker image.

## A real example

You press `⌘K` and type `rel`. The palette calls
`/api/v1/instruments/search?q=rel`. The server scans the master list for any
entry whose name or ticker contains `rel` — "Reliance Industries", "Reliance
Power", "Reliance Capital" all match. You pick one. The terminal opens
`/app/stocks/RELIANCE.NS`.

If you type `nifty`, you get the index tickers (`^NSEI`, `^BSESN`, etc.) because
they are also in the master file.

## What is in the file

The JSON has two top-level keys:

```json
{
  "stocks": {
    "Nifty 50": "^NSEI",
    "HDFC Bank": "HDFCBANK.NS",
    ...
  },
  "nifty50_sectors": {
    "IT": [["TCS.NS", "Tata Consultancy Services", 1200000], ...],
    ...
  }
}
```

- `stocks` — ordered dict of `human name → Yahoo ticker`. Insertion order is
  preserved; UI listings rely on it.
- `nifty50_sectors` — dict of `sector name → [[ticker, label, mcap], ...]`. The
  market-data module uses this for the sector performance heatmap.

## Where it lives in the codebase

- Backend code: `backend/app/modules/instruments/`
- Data file: `backend/app/modules/instruments/data/instrument_master.json`
- Backend dev notes: `backend/docs/instruments/`
- Frontend API client: `frontend/lib/api/instruments.ts`
- Frontend hook: `frontend/lib/hooks/use-instruments.ts`
- Consumers: search palette (`frontend/components/SearchPalette.tsx`), sidebar
  filter, sectors page

## Consumed by (frontend pages)

- [Search](../../pages/search/overview.md) — the ⌘K command palette. Every keystroke hits this.
- [Compare](../../pages/compare/overview.md) — symbol picker for 2–4 stocks.
- [Backtest](../../pages/backtest/overview.md) — symbol picker for the strategy form.
- [Paper trading](../../pages/paper-trading/overview.md) — symbol picker for orders.
- [Alerts](../../pages/alerts/overview.md) — symbol picker in the create form.
- [Markets](../../pages/markets/overview.md) — NSE quote tab symbol picker.
- [Sectors](../../pages/sectors/overview.md) — sector filter dropdown.

## Related pages in this folder

- [How it works](how-it-works.md) — the substring search algorithm, the lru_cache
  trick, the package-data loading.
- [Implementation](implementation.md) — file map, the two endpoints, adding a new
  symbol.