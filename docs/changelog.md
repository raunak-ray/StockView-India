# Changelog

Notable changes to the docs tree. Newest first.

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