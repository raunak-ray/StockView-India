# Changelog

Notable changes to the docs tree. Newest first.

## October 2026 — stored news sentiment on the stock page

The news module now serves the **stored** sentiment archive first and only
falls back to a live scrape for a stock we have never scraped.

### New

- `GET /api/v1/sentiment/insight` — one call for the whole news-and-mood
  card: the score, the 1M/3M/1Y/3Y breakdown, the strongest positive and
  negative stories, the latest articles and the technical layer. The response
  carries `isStoredData` so the UI can say where the numbers came from.
- The stock page gained two cards: **News over time** (the four period cards)
  and **Biggest stories** (the five strongest positive and negative stories).

### Changed

- `GET /sentiment/news` and `GET /sentiment/score` are **deprecated**. Their
  controllers are commented out in the router and the routes answer with a
  notice pointing at `/sentiment/insight`.
- The live scoring function now reports `isStoredData: false`; the stored path
  reports `true`.

### Updated

- `modules/sentiment/` — overview, how-it-works and implementation rewritten
  around the stored-first flow, with the request trace and the file map.
- `pages/stock-terminal/` — the news card section, the hooks table and the
  parallel-fetch diagram now point at `/sentiment/insight`.

## October 2026 — blockchain module

The blockchain module shipped, and the handbook gained a 14th module
folder plus updates to every index that counted modules.

### New

- `docs/modules/blockchain/` — `overview.md`, `how-it-works.md`,
  `implementation.md`, following the existing 3-file pattern.
  Covers the ×100 fixed-point scaling, the write path, the duplicate
  check, the auto-save pipeline, and the manual verification walkthrough.
- A **Blockchain terms** section in [glossary.md](glossary.md) —
  15 terms from "append-only ledger" to "duplicate suppression".
- A **Blockchain** section in [viva-questions.md](viva-questions.md) —
  11 questions, including the honest ones ("does it make the
  prediction *correct*?", "does it have tests?").
- A **Blockchain** section in [faq.md](faq.md) — 9 entries.
- **Option E** in [demo-guide.md](demo-guide.md) — the verification
  strip, with a failure path for the strip being unavailable.
- **Blockchain (optional)** in [setup.md](setup.md) — Ganache,
  `deploy.sh`, and a restart reminder. Marked optional because the rest
  of the project does not need Docker.

### Updated

- `architecture.md` — 13 → 14 modules, blockchain in the backend
  diagram and the code map, Ganache added to the big picture, plus a
  new `blockchain/` top-level folder in the tree.
- `modules/README.md` — new row, 13 → 14 modules, 39 → 42 files.
- `README.md`, `getting-started.md` — module counts.
- `glossary.md` — 13 → 14 modules.
- `demo-guide.md` — "pick two of the four" → "five"; the architecture
  pitch and the after-demo doc count.
- `pages/stock-terminal/` — the verdict card gained the blockchain
  strip, so the component line count, the file map, the hooks table,
  and three gotchas all changed.
- `viva-questions.md` — **corrected a false statement**: the old answer
  said the blockchain was "dropped by decision". It was dropped during
  planning and has since been implemented.
- `docs/README.md` — new known-issue entry covering the untested
  duplicate check.

### Corrections

- The module line-count total in `modules/README.md` was removed. It
  claimed 8,140 lines, but the actual total across the 13 modules was
  5,746 — several per-module figures in that table were also
  inflated (auth claimed 459, actual 294). Correcting all of them is
  a separate pass; the known-wrong total is gone rather than carried
  forward.

### Still missing

- `tests/test_blockchain.py`. Every other module has one. The
  duplicate check is nine chained equality comparisons and has no
  automated regression guard. Flagged in the module docs, the FAQ, the
  viva list, and `docs/README.md`.
- Line counts for the 13 pre-existing modules are still stale.
- Screenshots for the blockchain strip.

## April 2026 — full expansion

The docs were rewritten from a flat tree of 79 single-file stubs
into a structured tree of folders:

- **Before**: `docs/modules/<name>.md` — one short page per module.
  `docs/pages/<name>.md` — one short page per page. ~3,200 lines
  total, mostly stubs and code maps.
- **After**: `docs/<topic>/<name>/{overview,how-it-works,implementation}.md`
  — three focused files per topic, with diagrams, request traces,
  and gotchas. ~21,500 lines total.

### What changed

- **Backend modules** — 13 modules × 3 files = 39 files, 8,140
  lines. Each module now has an overview (what it is), a
  how-it-works (the algorithm with diagrams), and an
  implementation (file map + request traces).
- **Frontend pages** — 12 pages × 3 files = 36 files, 10,180
  lines. Same 3-file pattern.
- **Parent handbook** — 8 files expanded from 146 lines to
  ~1,800 lines. Includes architecture diagrams, the database
  schema, the setup troubleshooting, the demo failure paths, 30
  viva questions, and a 50-term glossary.
- **Index files** — `docs/modules/README.md` and
  `docs/pages/README.md` rewritten to link to the folder
  structure with one-line descriptions and line counts.
- **Screenshots** — placeholder folder created at
  `docs/screenshots/`. TBD: capture images for all 12 pages.
- **Bug documented** — the `lastPrice` vs `price` bug in
  `backend/app/modules/alerts/service.py` was found and
  documented in both the module docs and the page docs. The
  4-line fix is in
  [alerts/implementation.md](modules/alerts/implementation.md#the-fix-in-detail).

### Voice

The rewrite is in plain English, short sentences, real examples
(RELIANCE, TCS, INFY), no "leverages" / "seamlessly" /
"comprehensive", no AI-feel. Mermaid for flows (sequence for
lifecycle, class for schemas, state for status machines, flow
for branching).

### What was removed

- 13 leftover single-file `docs/modules/*.md` (replaced by the
  folder structure).
- 12 leftover single-file `docs/pages/*.md` (replaced by the
  folder structure).
- The "API reference" section in each module (folded into
  `how-it-works.md`).
- The "Examples" section in each module (folded into
  `overview.md` and `how-it-works.md`).

### What was added

- The 3-file pattern (overview, how-it-works, implementation).
- 1–3 mermaid diagrams per file.
- Real-world examples (RELIANCE, TCS, INFY, etc.) in every
  file.
- Request traces (mermaid sequence) for every major flow.
- The "Common gotchas" section in every `implementation.md`.
- Cross-links between module docs and the pages that consume
  them.
- The "known issues" section in the parent README, calling out
  the alerts bug, in-memory stores, and ticker renames.
- The `docs/changelog.md` (this file).
- The `docs/screenshots/` placeholder folder.
- The `docs/faq.md` (common questions beyond the viva list).

## Future work

- Capture screenshots for all 12 pages.
- Add a "How to add a new indicator" recipe (analytics module).
- Add a "How to add a new backend endpoint" recipe.
- Add a "How to deploy to production" guide (Docker Compose →
  Kubernetes, or just Docker Compose on a single VM).
- Add API reference docs (probably generated from the OpenAPI
  schema at `/openapi.json`).
- Add a "Common tasks" cheat-sheet that points at the relevant
  per-module `implementation.md` section.

## Related

- [README.md](README.md) — the entry point.
- [modules/README.md](modules/README.md) — the backend index.
- [pages/README.md](pages/README.md) — the frontend index.