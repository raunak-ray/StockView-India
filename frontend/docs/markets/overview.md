# Markets — Overview

**Plain words:** the NSE India data hub — four tabs of exchange-level data
Yahoo doesn't provide well.

## The four tabs

1. **NSE Quote** — search any instrument (the search waits until you stop
   typing), see the official NSE quote card, auto-refreshing every 60s.
2. **FII / DII** — ₹ crores foreign (FII) and domestic (DII) institutions
   bought/sold: flow cards, sparkline, session table. If live sources are
   unreachable, static numbers load and a yellow notice says so.
3. **Advances / Declines** — how many stocks rose vs fell: stat tiles plus a
   ratio bar. A wide gap means a strong market day.
4. **Options / PCR** — pick an index chip or type an equity: PCR & max-pain
   cards and the full option chain with strike filter, near-ATM window and
   pagination.

## Good to know

On networks outside India, NSE blocks API calls → the options tab may show
"unavailable". Documented limitation, not a bug; quotes and FII/DII have
fallbacks that usually still work. Each tab caches and refreshes on its own
schedule.

## Where the code lives

`frontend/app/(app)/app/markets/` — page + one component per tab +
`constants.ts`. Client: `lib/api/nse.ts`; hooks: `lib/hooks/use-nse.ts`,
`use-debounce.ts`.
