# Sentiment — Endpoints

Both require login.

| Method & path | What it does |
|---|---|
| `GET /api/v1/sentiment/news?symbol=&max_items=` | Latest headlines (default 8, max 20), cached 10 min |
| `GET /api/v1/sentiment/score?symbol=&interval=&period=` | News mood + chart mood + per-headline detail |

## Score response, field by field

- `finbert_available` — whether the ML model is installed (capability flag).
- `news.score / label` — −1…+1 and BULLISH / BEARISH / NEUTRAL.
- `news.detail[]` — every headline with its own tone label and score
  (the website shows these as coloured badges).
- `technical.score / label / raw_score` — chart mood before and after
  normalisation.
- `technical.signals[]` — the ten rule checks: name, tone, message, weight.

## Headline fetch order (parity with the old app)

1. Yahoo Finance RSS (India edition)
2. Google News RSS fallback
3. yfinance `.news`

Each attempt is best-effort; an empty result is normal on quiet networks —
the mood simply shows NEUTRAL.
