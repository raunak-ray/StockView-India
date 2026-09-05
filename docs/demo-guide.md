# Demo guide (7 minutes)

A walkthrough script for showing the project to an examiner, a
prospective employer, or a class. The 7-minute timing assumes nothing
goes wrong — the [failure paths](#failure-paths) section below covers
the 4 most common things that can break and how to recover.

## Before you start

1. **Pre-warm the demo data.** Open the dashboard and the
   stock-terminal for RELIANCE.NS **at least 60 seconds** before
   the demo. This caches the market-data and analytics responses
   in Redis and warms the ML models for the symbol you'll demo.
2. **Open the API docs in a second tab**:
   `http://localhost:8000/docs`. This shows the backend's Swagger
   UI and lets you answer "how does that work" questions live.
3. **Have a backup stock in mind.** If RELIANCE is having a flat
   day, switch to TCS or INFY.
4. **Have a backup page in mind.** If the stock terminal is slow,
   switch to the dashboard (it has its own data already cached).

## The script

### 1. Intro (1 min)

> "StockView India is a stock-analysis site for Indian markets. You
> search any NSE stock, get a price chart and a one-word verdict
> (BUY / HOLD / SELL) with the reasons listed, and a set of
> practise tools with fake money. The site runs on a Next.js
> frontend, a FastAPI backend, PostgreSQL for accounts, and Redis
> for caching. Prices come from Yahoo Finance; options and FII/DII
> flows come from NSE India."

End on a pause. Let the examiner ask a question. If they don't, move
on.

### 2. Dashboard to stock (2 min)

Log in as `demo / demo123`. The dashboard loads at `/app`.

- **Point at the Nifty/Sensex/Bank Nifty cards** (top of the page).
  "These are the three main Indian indices, refreshed every minute.
  Green means up today, red means down."
- **Point at the movers panel** (left or right, varies by viewport).
  "Top gainers and top losers — picked from the Nifty 500 universe
  by today's percent change."
- **Press ⌘K** (or Ctrl+K). The command palette opens. Type
  "reliance". ↵. The page navigates to RELIANCE.NS.

On the stock terminal:

- **Read the price and day change** at the top. "This is the live
  price — last traded — with today's change and percent change."
- **Point at the chart**. "Daily candles, 1 year of history. Green
  closed up, red closed down. The 20-day and 50-day averages are
  drawn on top."
- **Point at the verdict card** (BUY / HOLD / SELL badge). "The
  verdict is computed by three layers — technical rules, an ML
  prediction, and news mood — each with a weight. The badge colour
  matches the verdict."
- **Read two "Why" lines**. "The verdict includes the top 2–3
  reasons it was given. The reasoning is plain English, not
  jargon."

### 3. Depth (2 min, pick two of the four)

Show two of the following four, in any order. Each takes about 1
minute.

**Option A — Chart with indicators (1 min)**
- "Switch to the RSI sub-chart. RSI above 70 means overbought,
  below 30 means oversold."
- "Switch to the MACD sub-chart. When the orange line crosses the
  blue line, that's a momentum shift."

**Option B — AI card (1 min)**
- Scroll to the AI card. "This is a separate model that predicts
  tomorrow's price. It uses an ensemble of XGBoost, LightGBM, and
  CatBoost, with a scikit-learn fallback if those aren't installed."
- "The accuracy number is the model's win rate on the last 20% of
  the history. The walk-forward validation prevents cheating."

**Option C — News card (1 min)**
- Scroll to the news card. "Headlines about this stock, scored for
  mood by FinBERT — a financial-distilbert model. Green badge =
  positive news, red = negative, grey = neutral."
- "If FinBERT isn't enabled, the score comes from a 10-rule
  technical mood engine — the trade-off is speed."

**Option D — Backtest (1 min)**
- Navigate to `/app/backtest`. Pick RELIANCE, SMA Cross strategy,
  1 year. Click "Run backtest".
- "This runs the strategy against historical data. The chart at
  the top is the equity curve — your ₹1,00,000 grew to ₹X. The
  numbers below are CAGR, max drawdown, Sharpe, win rate, and
  more."

### 4. Honesty (1 min)

> "Two things to be honest about. First, prices come from Yahoo
> Finance, and options and FII/DII flows come from NSE India. NSE
> sometimes blocks non-India IPs — if you see a 502 on the markets
> page, that's expected. Yahoo-based pages still work fine.
> Second, the predictions are educational, not financial advice. A
> model's 60% win rate on history doesn't mean it'll work in
> practice."

This builds trust. Examiners appreciate honesty about limitations.

### 5. Architecture (1 min)

> "On the frontend, it's Next.js with the App Router. Each page is
> a server component that hands off to client components for the
> data fetching. The data layer is React Query with single-flight
> session refresh — when the access token expires, the api client
> refreshes once and retries the request, so the UI never sees a
> 401. On the backend, it's FastAPI with one module per concern —
> auth, market data, analytics, signals, ML, backtesting, alerts,
> portfolio, NSE, compare. Postgres holds accounts and
> watchlists. Redis caches the upstream responses. The signals
> module does a 3-layer fusion — technical rules, ML prediction,
> and news mood — each with a weight. Missing pieces re-weight
> dynamically so the verdict is always well-defined."

End on a stop. Take questions. If none, offer the source code tour.

## Failure paths

The 7-minute script assumes everything works. In real demos, things
break. Here's how to recover.

### NSE tabs error with 502

**Symptom**: The markets page (FII/DII, advances/declines, options)
shows a 502 error.

**Recovery**: Switch to a Yahoo-based page — the dashboard, the
stock terminal, the sectors page, the backtest, or the paper-trading
page. None of these depend on NSE.

**What to say**: "NSE's API blocks some networks. The fallback
chain is configured — it tries Trendlyne, then a static fixture —
but the live data is preferred when reachable."

### Alerts list is empty / all in "Triggered"

**Symptom**: You set an alert and within 30 seconds it moves to
"Triggered" with a red badge.

**Recovery**: This is the known `lastPrice` bug in
`backend/app/modules/alerts/service.py`. The fix is documented in
`docs/modules/alerts/implementation.md`.

**What to say**: "There's a known issue where the alert evaluator
looks up the wrong key from the market-data response. The 4-line
fix is in the implementation docs. Until it's applied, every alert
fires immediately. I'm going to use a different feature for the
rest of the demo."

### ML prediction takes 30+ seconds

**Symptom**: The AI card on the stock terminal shows a spinner for
30–60 seconds on the first load.

**Recovery**: Wait. It's training the model. Once trained, all
subsequent calls for the same symbol return in ~50ms.

**What to say**: "The ML module trains on first call per symbol. It
uses an ensemble of XGBoost, LightGBM, and CatBoost. The first call
pays the training cost; subsequent calls hit the in-memory cache."

### Chart is empty / no data

**Symptom**: The chart on the stock terminal shows "No data" or
"Loading…" indefinitely.

**Recovery**: yfinance rate limit. Wait 10 minutes. In the meantime,
switch to a different stock or a different page.

**What to say**: "Yahoo Finance rate-limits aggressive callers. The
5-tier cache in the market-data module helps in normal use, but a
fresh start with many concurrent requests can hit the limit. The
backend falls through to the upstream call after each cache miss."

### Login fails with 429

**Symptom**: The login form returns "Too many requests" after a
few attempts.

**Recovery**: Wait 1 minute. The rate limit is 10 attempts per
minute per IP.

**What to say**: "Rate limit on the login endpoint — 10 attempts per
minute per IP, to prevent brute force."

### Frontend shows "Failed to fetch"

**Symptom**: All pages show "Failed to fetch" or spinner forever.

**Recovery**: The backend is not running. Open the terminal where
`uvicorn` was started and check for errors. If the process died,
restart it.

**What to say**: "The backend died — let me restart it. (Restart.)"
This is normal and quick. Don't panic.

## After the demo

- **Take a few questions.** Common questions are in [Viva questions](viva-questions.md).
- **Open the source code** if asked. Each per-module and per-page
  doc has the file map; you can navigate to any file quickly.
- **Show the docs.** The `docs/` folder has 13 backend module docs
  and 12 frontend page docs, each with overview, how-it-works, and
  implementation files. ~21,500 lines of documentation.

## Related

- [Getting started](getting-started.md) — the 5-minute first-time user walkthrough.
- [Viva questions](viva-questions.md) — questions examiners commonly ask.
- [Architecture](architecture.md) — the diagram for the "how does it fit together" question.
- [Glossary](glossary.md) — for any term the examiner asks about.