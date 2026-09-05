# Frontend pages

One folder per page. Each folder has three files: a short **overview**
(what it is), a **how-it-works** walkthrough (data flow, components,
state), and an **implementation** file (file map, every component,
hooks, request traces).

| Page | What it does | Docs |
|---|---|---|
| **Landing** | `/` public homepage — hero, features, how-it-works, team, footer | [overview](landing/overview.md) · [how it works](landing/how-it-works.md) · [implementation](landing/implementation.md) · 664 lines |
| **Auth** | `/login`, `/register` — sign-in / sign-up with zod validation, single-flight session refresh | [overview](auth/overview.md) · [how it works](auth/how-it-works.md) · [implementation](auth/implementation.md) · 971 lines |
| **Dashboard** | `/app` home screen — greeting, index cards, market movers, watchlist | [overview](dashboard/overview.md) · [how it works](dashboard/how-it-works.md) · [implementation](dashboard/implementation.md) · 775 lines |
| **Stock terminal** | `/app/stocks/[symbol]` — chart, indicators, verdict, news, AI prediction | [overview](stock-terminal/overview.md) · [how it works](stock-terminal/how-it-works.md) · [implementation](stock-terminal/implementation.md) · 1,194 lines |
| **Markets** | `/app/markets` — 4 tabs: NSE quote, FII/DII, advances/declines, options/PCR | [overview](markets/overview.md) · [how it works](markets/how-it-works.md) · [implementation](markets/implementation.md) · 971 lines |
| **Sectors** | `/app/sectors` — squarified treemap, performance bars, sector drill-down | [overview](sectors/overview.md) · [how it works](sectors/how-it-works.md) · [implementation](sectors/implementation.md) · 893 lines |
| **Compare** | `/app/compare` — 2–4 symbols, normalised chart, snapshot cards, comparison table | [overview](compare/overview.md) · [how it works](compare/how-it-works.md) · [implementation](compare/implementation.md) · 925 lines |
| **Backtest** | `/app/backtest` — 6 strategies, equity curve, monthly heatmap, trade log | [overview](backtest/overview.md) · [how it works](backtest/how-it-works.md) · [implementation](backtest/implementation.md) · 888 lines |
| **Paper trading** | `/app/paper-trading` — ₹1L virtual portfolio, buy/sell ticket, positions, orders | [overview](paper-trading/overview.md) · [how it works](paper-trading/how-it-works.md) · [implementation](paper-trading/implementation.md) · 928 lines |
| **Alerts** | `/app/alerts` — price alarm manager, Watching + Triggered lists | [overview](alerts/overview.md) · [how it works](alerts/how-it-works.md) · [implementation](alerts/implementation.md) · 792 lines · **known bug** |
| **Settings** | `/app/settings` — read-only profile card (username, role, user ID, member since) | [overview](settings/overview.md) · [how it works](settings/how-it-works.md) · [implementation](settings/implementation.md) · 513 lines |
| **Search** | ⌘K command palette — global instrument search, mounted in the app shell | [overview](search/overview.md) · [how it works](search/how-it-works.md) · [implementation](search/implementation.md) · 666 lines |

**Total: 12 pages · 36 files · 10,180 lines.**

The app shell (sidebar, topbar, mobile nav) is documented inside the
[Dashboard implementation](dashboard/implementation.md) — the shell
wraps every `/app/*` page. Authentication (route guard, session
refresh, login form) is documented in [Auth](auth/overview.md).

## How to read a page

If you want a **5-minute overview** — read `overview.md` only.

If you want to **understand the data flow** — read `how-it-works.md`. It
has the per-section flow, the state, the per-component render logic,
and diagrams.

If you want to **modify the code** — read `implementation.md`. It has
the file map, every component, the hooks used, request traces, and
gotchas. Pair with the actual source files in
`frontend/app/(app)/app/<page>/` (or for landing/auth, in
`frontend/app/`).

For deeper notes (component rationale, styling decisions, accessibility
notes), check `frontend/docs/<page>/` — the per-page dev notes that
live alongside the source code.