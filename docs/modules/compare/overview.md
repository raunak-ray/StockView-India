# Compare — what it is

The compare module is a **side-by-side comparison of 2–4 symbols** over a
chosen period. The key trick is **price normalisation** — every symbol is
rebased to 100 on the first common trading day, so a ₹3,000 stock and a
₹400 stock share the same chart axis fairly.

It is the smallest module in the project. One router, one service, one
schema. There is no DB, no caching of its own (the upstream `market_data`
caches handle that), and no business logic beyond the normalisation math.

## What you can do with it

- Compare **2 to 4 symbols** at a time.
- Pick the period: `1mo`, `3mo`, `6mo`, `1y`, `3y`, or `5y`.
- Get per-symbol **snapshot data** (last price, change %, volume, market cap,
  P/E, 52-week range, SMA-20/50, RSI, MACD).
- Get the **normalised overlay** for charting — a list of `{date, values}`
  where every symbol starts at 100 on day 0 and grows or shrinks from there.

## How normalisation works

A ₹3,000 stock and a ₹400 stock cannot share an axis. The compare module
solves this by re-scaling each symbol to 100 at the start:

```mermaid
flowchart LR
    A[RELIANCE.NS closes over 1y] --> Start[find common start date]
    B[TCS.NS closes over 1y] --> Start
    Start --> Rebase[every symbol rebased to 100 at start]
    Rebase --> Out[overlay: date and {RELIANCE.NS: 100, 102, 105, ...}, {TCS.NS: 100, 99, 101, ...}]
```

After rebase:

- A symbol that ended 12% above its start → ends at 112.
- A symbol that ended 5% below → ends at 95.
- A symbol that ended flat → ends at 100.

The chart plots all the rebased series on one Y-axis. The relative shape of
each line shows the **rate of return**, not the absolute price.

## A real example

You compare RELIANCE.NS, TCS.NS, and INFY.NS over 1 year:

```json
{
  "symbols": [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "last_price": 2945.30,
     "change_pct": 0.42, "volume": 8500000, "market_cap": 1990000000000,
     "pe_ratio": 25.4, "high_52w": 3024.50, "low_52w": 2220.10,
     "sma_20": 2890.20, "sma_50": 2820.50, "rsi": 62.3,
     "macd": 12.45, "macd_signal": 10.20, "macd_hist": 2.25},
    {"symbol": "TCS.NS", ...},
    {"symbol": "INFY.NS", ...}
  ],
  "normalized": [
    {"date": "2025-04-17", "values": {"RELIANCE.NS": 100.0, "TCS.NS": 100.0, "INFY.NS": 100.0}},
    {"date": "2025-04-18", "values": {"RELIANCE.NS": 100.8, "TCS.NS": 100.2, "INFY.NS": 100.5}},
    ...
    {"date": "2026-04-17", "values": {"RELIANCE.NS": 112.0, "TCS.NS": 105.0, "INFY.NS": 108.0}}
  ],
  "period": "1y"
}
```

The chart plots three lines that all start at 100 and diverge from there.
RELIANCE is the strongest performer (+12%), INFY is in the middle (+8%),
TCS is the weakest (+5%).

## The snapshot data

For each symbol, the snapshot includes:

- **Price**: last price, change %
- **Volume**: today's volume
- **Valuation**: market cap, P/E ratio
- **Range**: 52-week high and low
- **Trend**: SMA-20, SMA-50
- **Momentum**: RSI, MACD line, MACD signal, MACD histogram

The snapshot comes from `market_data.get_info` (yfinance metadata) plus a
local compute of SMA/RSI/MACD from the history. This is **independent** of
the `analytics` module — the compare module computes its own indicators so
it can be used without the analytics stack.

## Why a separate module

- **Side-by-side comparison is its own use case.** It is not the same as
  viewing one stock on its own. The comparison view is its own page, its
  own URL, its own workflow.
- **Normalisation is the value-add.** Without it, comparing a ₹3,000 stock
  to a ₹400 stock is meaningless.
- **Small enough to fit in your head.** One file, ~180 lines.

## Where it lives in the codebase

- Backend code: `backend/app/modules/compare/`
- Backend dev notes: `backend/docs/compare/`
- Source: `market_data.get_info` + `market_data.get_history`
- Frontend API client: `frontend/lib/api/compare.ts`
- Frontend hook: `frontend/lib/hooks/use-compare.ts`
- Frontend consumer: `/app/compare` page

## Consumed by (frontend pages and other modules)

- [Compare](../../pages/compare/overview.md) — the only consumer. The 2–4 symbol
  picker, the normalised chart, the snapshot cards, and the comparison table.
- Module: [Market data](../market-data/overview.md) — fetches the per-symbol
  historical data and company info.

## Related pages in this folder

- [How it works](how-it-works.md) — the period map, the common-date set
  intersection, the normalisation math, the in-place indicator compute.
- [Implementation](implementation.md) — file map, every function, the
  `_NAMES` fallback, gotchas.