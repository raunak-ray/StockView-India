# News — what it is

The news module collects **headlines about Indian stocks from Google News** and
stores them in a **separate news database** (not the app database). It is the
data source for the sentiment module and, through the signals fusion, for the
news leg of the stock verdict.

Nothing in the app talks to Google News directly. Every headline, every article
body, every scrape run passes through this module.

## What you can do with it

- **Scrape** one stock over a look-back window (1–3650 days) via
  `POST /api/v1/news/scrape` or the CLI `python -m scripts.scrape_news`.
- **Read** stored headlines for a symbol via `GET /api/v1/news/articles`.
- **Inspect coverage** across the universe via `GET /api/v1/news/coverage`.
- **Run the sentiment scorer** (`python -m scripts.score_sentiment --score --aggregate`)
  over the stored corpus.

## Why it exists as a separate module

- **Isolated database.** News is the bulkiest, fastest-growing data in the
  project. It lives in its own Postgres instance (`SV_DATABASE_NEWS_URL`) so
  the app database stays small and `init_db()` never creates news tables there.
- **One stock per run.** Google News throttles by IP. A run covering all 86
  stocks invites the 503 that kills the crawl; a single-symbol run either
  finishes or fails cleanly and can be re-run.
- **Idempotent.** Dedupe is on `(content_hash, symbol)` where `content_hash`
  is a sha256 of the normalised title. Re-running a finished stock reports
  `articles stored: 0`.
- **Checkpointed.** Progress is committed every 30 days, so a crashed run
  keeps everything it had already written; a resume only fetches the days
  still missing.

## The scrape universe

**86 stocks** — Nifty 100 members that also exist in the app's 646-stock
instrument master. 14 Nifty 100 members are excluded because there is no
ticker to store them against (see `plan/stock_todo.md` "Not covered").

Defined in `backend/app/modules/news/data/nifty100_symbols.json` (snapshot
2026-10-02) and exposed via `symbols.targets()`.

## Where it lives in the codebase

- Backend code: `backend/app/modules/news/`
- Backend dev notes: (this folder's siblings)
- News database connection: `backend/app/core/news_db.py`
- CLI scraper: `backend/scripts/scrape_news.py`
- CLI scorer: `backend/scripts/score_sentiment.py`
- Frontend API client: `frontend/lib/api/news.ts` (if present)
- Progress tracker: `plan/stock_todo.md`

## Consumed by

- [Sentiment](../sentiment/overview.md) — scores the stored corpus with FinBERT
  and aggregates per symbol / period.
- [Signals](../signals/overview.md) — news leg of the 3-layer fusion verdict.

## Related pages in this folder

- [How it works](how-it-works.md) — the scrape ladder, relevance filter,
  checkpointing, body extraction, rate limiting.
- [Implementation](implementation.md) — file map, every function, request
  traces, schemas.
