# News — implementation

## File map

| File | Purpose |
|---|---|
| `backend/app/modules/news/__init__.py` | Package marker |
| `backend/app/modules/news/models.py` | `NewsArticle` (news_articles table) |
| `backend/app/modules/news/schemas.py` | Pydantic request/response models |
| `backend/app/modules/news/router.py` | FastAPI router (`/news`) |
| `backend/app/modules/news/service.py` | Scrape orchestration, filters, checkpointing |
| `backend/app/modules/news/sources.py` | Google News RSS client, rate limiting |
| `backend/app/modules/news/extractor.py` | Article body extraction |
| `backend/app/modules/news/symbols.py` | Scrape universe (86 targets) |
| `backend/app/modules/news/data/nifty100_symbols.json` | Checked-in snapshot |
| `backend/app/modules/news/sentiment/` | FinBERT scoring + aggregation + trend API |
| `backend/scripts/scrape_news.py` | CLI entry point |
| `backend/scripts/score_sentiment.py` | CLI scorer |
| `backend/app/core/news_db.py` | Isolated news database engine |

## Key functions

### service.py
- `content_hash(title)` — sha256 of normalised title.
- `is_boilerplate(article)` — drops ticker/price-ticker noise.
- `is_relevant(article, target)` — distinctive-token gate.
- `_distinctive_tokens(target)` — derives tokens from company name.
- `store_articles(session, articles)` — deduped insert.
- `fill_bodies(session, articles, client)` — body extraction for recent window.
- `scrape_symbol(target, days)` — one symbol end to end.
- `_day_chunks(start, end, size=30)` — 30-day checkpoint windows.
- `_collect_for_windows(...)` — fetch + filter per window.
- `scrape(symbol, days)` — public entry; validates, orchestrates, returns `ScrapeStats`.

### sources.py
- `configure_rate_limit(rps)` — set request pace.
- `fetch_articles(client, query, start, end)` — one RSS request.
- `parse_rss(xml)` — RSS -> `RawArticle`.
- `preflight(client)` — single request to confirm the IP is not blocked.

### extractor.py
- `resolve_url(client, url)` — follow Google News redirect.
- `extract_body(html)` — pull article text from publisher HTML.
- `fetch_body(client, url)` — pace + resolve + extract.

### symbols.py
- `targets()` — list of 86 `Target`.
- `by_symbol(symbol)` — lookup (accepts suffixed or bare).
- `coverage()` — universe metadata.

## Schemas

`ScrapeRequest { symbol, days }`, `ScrapeResult`, `NewsArticleOut`,
`NewsArticleListResponse`, `NewsCoverageResponse`.

## Sentiment

`backend/app/modules/news/sentiment/` adds:
- `models.py` — `NewsArticleSentiment`, `NewsSentimentPeriod`, `StockNewsSentiment`.
- `service.py` — `score_article`, `score_pending`, `aggregate_symbols`,
  `get_trend`, `get_ranking`, `scoring_status`.
- `schemas.py` — trend/ranking/status response models.
- `router.py` — `/news/sentiment/*` endpoints.

## CLI

```
python -m scripts.scrape_news --symbol RELIANCE.NS --days 1095
python -m scripts.scrape_news --symbol RELIANCE.NS --days 7
python -m scripts.scrape_news --list-universe
python -m scripts.scrape_news_all                # refresh all stored symbols, 30 days
python -m scripts.scrape_news_all --days 7
python -m scripts.score_sentiment --score --aggregate
```

Exit codes: 0 success, 2 bad args, 3 upstream unavailable (throttled).

## Database

News tables live in the isolated news database (`SV_DATABASE_NEWS_URL`):
- `news_articles` — scraped headlines (deduped).
- `news_article_sentiment` — per-article FinBERT scores.
- `news_sentiment_period` — per symbol × period (1M/3M/1Y/3Y) aggregates with price.
- `stock_news_sentiment` — per-symbol summary for ranking.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/news/scrape` | Scrape one stock |
| POST | `/api/v1/news/scrape-all` | Refresh all stored symbols (optional `days`, default 30) |
| GET | `/api/v1/news/articles` | Stored headlines for a symbol |
| GET | `/api/v1/news/coverage` | Universe + stored counts |
| GET | `/api/v1/news/sentiment/status` | Scoring progress |
| GET | `/api/v1/news/sentiment/ranking` | All scored stocks, bullish first |
| GET | `/api/v1/news/sentiment/{symbol}/trend` | 1M/3M/1Y/3Y sentiment + price series |
