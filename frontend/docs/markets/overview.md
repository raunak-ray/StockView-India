# Markets — Overview

**Plain words:** the NSE India data hub — four full-width tabs of
exchange-level data Yahoo doesn't offer well.

## The four tabs (lucide icons, no emojis)

1. **NSE Quote** — search any instrument (the search waits until you stop
   typing), see the official NSE quote card, auto-refreshing every 60s.
2. **FII / DII** — ₹ crores foreign (FII) and domestic (DII) institutions
   bought/sold: two flow cards with sparklines, then **recent sessions as
   paginated cards** (4 per page).
3. **Advances / Declines** — how many Nifty-50 stocks rose/fell: stat tiles
   with icons plus a ratio bar.
4. **Options / PCR** — index chips or a custom equity: Spot / PCR / max-pain
   cards and the option chain table with strike filter, near-ATM window and
   a pager.

## Tooltips everywhere jargon appears

Hover any small **ⓘ** for a one-line plain-English explanation: PCR, max
pain, VWAP, OI, CE/PE, A/D ratio, near-ATM, FII/DII.

## Good to know

- No data-source or cache notices are shown — the interface stays quiet and
  clean; failures simply say "unavailable, retry".
- Outside India, NSE often blocks API calls → the options tab may show
  "unavailable". Documented limitation, not a bug.

## Where the code lives

`frontend/app/(app)/app/markets/` — page + one component per tab + shared
`pager.tsx`. Client: `lib/api/nse.ts`; hooks: `lib/hooks/use-nse.ts`,
`use-debounce.ts`.
