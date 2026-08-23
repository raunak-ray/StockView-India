# Markets — Overview

**Plain words:** the NSE India data hub — four full-width tabs of
exchange-level data Yahoo doesn't offer well.

## The four tabs (lucide icons)

1. **NSE Quote** — search any instrument (waits until you stop typing), see
   the official NSE quote card, refreshing every 60s.
2. **FII / DII** — ₹ crores foreign (FII) and domestic (DII) institutions
   bought/sold: flow cards with sparklines, then **sessions as paginated
   cards**.
3. **Advances / Declines** — how many Nifty-50 stocks rose/fell: stat tiles
   plus a ratio bar.
4. **Options / PCR** — index chips or a custom equity: Spot / PCR / max-pain
   cards and the chain table with strike filter, near-ATM window, pager.

## Tooltips everywhere jargon appears

Hover any small **ⓘ** for a one-line explanation: PCR, max pain, VWAP, OI,
CE/PE, A/D ratio, near-ATM, FII/DII.

## Good to know

- No data-source or cache notices — the interface stays quiet; failures
  just say "unavailable, retry".
- Outside India, NSE often blocks API calls → the options tab may show
  "unavailable". Documented limitation, not a bug.

## Where the code lives

`frontend/app/(app)/app/markets/` — page + one component per tab + shared
`pager.tsx`. Client: `lib/api/nse.ts`; hooks: `lib/hooks/use-nse.ts`,
`use-debounce.ts`.
