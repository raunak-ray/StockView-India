# StockView India — Handbook

Documentation for the whole project. Start with [Getting started](getting-started.md)
for a 5-minute first-time walkthrough; look up the rest as needed.

**Last updated**: April 2026.
**Handbook size**: ~21,500 lines across 87 files.

## Where to start

- **New to the project?** [Getting started](getting-started.md) — log
  in and open your first stock in 5 minutes.
- **Setting it up locally?** [Setup](setup.md) — install
  prerequisites, run Docker, start the backend and frontend, with
  troubleshooting for the 6 most common issues.
- **Demoing it to someone?** [Demo guide](demo-guide.md) — the
  7-minute script with failure paths and recovery lines.
- **Preparing for a viva?** [Viva questions](viva-questions.md) — 30
  common questions grouped by topic, with short answers.

## Reference

- **[Glossary](glossary.md)** — ~50 stock and project terms, one
  line each, grouped by topic. The first place to look for any
  term you don't recognise.
- **[Architecture](architecture.md)** — the diagram and request
  lifecycle. The "how does it fit together" answer.
- **[Database](database.md)** — the schema, the tables, the
  migration plan, what is and isn't persisted.

## Detailed docs

- **[Backend modules](modules/)** — 13 modules, each in a folder
  with three files: `overview.md` (what it is), `how-it-works.md`
  (the algorithm), `implementation.md` (the file map and request
  traces). **39 files, 8,140 lines.**
- **[Frontend pages](pages/)** — 12 pages, the same 3-file
  pattern. **36 files, 10,180 lines.**

## Developer notes

- **`backend/docs/`** — per-module developer notes that live
  alongside the source code. Used by the team for architecture
  decisions, formula derivations, and known limitations.
- **`frontend/docs/`** — per-page developer notes. Component
  rationale, styling decisions, accessibility notes.

## Known issues

- **Alerts `lastPrice` vs `price`** — the alert evaluator in
  `backend/app/modules/alerts/service.py:90` reads
  `quote.get("lastPrice", alert.price)`, but the market-data
  response uses the key `price`. Every active alert fires
  immediately on the next polling cycle. The fix is a 4-line
  change documented in
  [alerts/implementation.md](modules/alerts/implementation.md#the-fix-in-detail).
  Flagged in `plan/todo.md`.
- **In-memory stores** — alerts and paper trading are kept in
  per-process dicts. A server restart wipes the data. The
  PostgreSQL migration is in `plan/todo.md` Phase A.
- **TATAMOTORS / ZOMATO renames** — the live tickers in 2026 are
  `TMPV.NS` and `ETERNAL.NS` (not `TATAMOTORS.NS` / `ZOMATO.NS`).
  Both legacy tickers still work via yfinance's alias map, but new
  searches should use the new names. See the [Market data
  module](modules/market-data/overview.md) for the maintenance
  note.

## How this handbook is organised

Each module and each page follows the same 3-file pattern:

1. **`overview.md`** (~60–150 lines) — what it is, in plain
   English, with one real-world example. Read this first.
2. **`how-it-works.md`** (~120–270 lines) — the data flow, the
   math, the state machine, the per-section flow. Read this to
   understand the algorithm.
3. **`implementation.md`** (~200–320 lines) — the file map, every
   function, request traces, common gotchas, and the fix for known
   bugs. Read this to modify the code.

The full pattern is documented in [modules/README.md](modules/README.md#how-to-read-a-module)
and [pages/README.md](pages/README.md#how-to-read-a-page).

## Contributing

Found a typo? An out-of-date fact? A missing term? Open a PR with
the fix — most updates are one-liners. For structural changes
(new files, reorganising sections), discuss first in the team's
docs channel.

The docs are reviewed as part of every release. The reviewer
checks:

- Links resolve to existing files.
- Code blocks reference real file paths.
- Diagrams are accurate and use the project's mermaid conventions.
- No "leverages", "seamlessly", "comprehensive", or other AI-feel
  words. The voice is short, direct, and specific.