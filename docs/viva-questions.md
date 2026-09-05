# Viva questions

A cheat sheet of questions examiners commonly ask, grouped by topic,
with short answers. Each answer is the one-line version — see the
linked doc for the full technical detail.

## What it is

- **What is StockView?** A stock-analysis site for India: charts, one
  verdict per stock, practise tools. [Demo guide](demo-guide.md).
- **Who is it for?** Retail Indian investors who want a single-screen
  view of a stock — price, indicators, news mood, AI prediction,
  and a verdict — without juggling 5 separate apps.
- **Is this financial advice?** No. Every prediction is labelled
  educational. The "BUY / HOLD / SELL" verdict is a model output, not
  a recommendation.
- **Where is the blockchain from the old plan?** Dropped by decision;
  the old prototype code remains only in the reference-only `app.py`.

## Architecture

- **What's the stack?** Next.js 15 (App Router) on the frontend, FastAPI
  on the backend, PostgreSQL 16 for storage, Redis 7 for cache. See
  [Architecture](architecture.md).
- **Why Next.js over plain React?** Server components for the initial
  render, built-in routing, and the proxy.ts for edge-level auth
  guards.
- **Why FastAPI over Flask or Django?** Async-native (no GIL contention
  for I/O), Pydantic-validated request/response, and auto-generated
  OpenAPI docs at `/docs`.
- **How does a request flow from browser to database?** Browser →
  proxy.ts (auth check) → Next.js (render) → React Query hook → api
  client → FastAPI router → service → PostgreSQL / Redis / yfinance.
  See [Architecture](architecture.md#a-request-lifecycle) for the
  sequence diagram.
- **How would you scale this for 1000 users?** The bottleneck is the
  market-data endpoint hitting yfinance. Add a request-coalescing
  layer (N concurrent requests for the same symbol → 1 upstream call),
  move the cache to a shared Redis, and run multiple backend instances
  behind a load balancer.
- **How do you handle rate limiting on the backend?** The `core/security.py`
  has a `slowapi` limiter with per-IP limits: 10/minute on login,
  60/minute on default endpoints. Exceeding the limit returns 429.

## Data sources

- **Where do prices come from?** Yahoo Finance via the `yfinance`
  Python library. Options and FII/DII flows come from NSE India (with
  fallback to Trendlyne, then a static fixture).
- **Why not use a paid data API like Bloomberg?** Cost. The demo
  uses free sources to keep the project self-contained. For
  production, paid APIs give better latency and reliability.
- **How fresh is the data?** Yahoo's free tier has a 15-minute delay
  for some markets. NSE's free endpoint is real-time but rate-limited.
  The 5-tier cache (60s for quotes, 300s for FII/DII) further reduces
  upstream calls.
- **How do you handle index renames (TATAMOTORS → TMPV)?** The
  instruments JSON is the source of truth — when a ticker renames,
  update the JSON and the cache invalidates. NSE-specific code uses
  the rename map in `backend/app/modules/nse/service.py`.

## ML and signals

- **How is the verdict computed?** Three layers: technical rules
  (45%), ML prediction (40%), news mood (15%). Each layer outputs a
  score; the weighted sum is the verdict. Missing pieces re-weight.
  See [Signals](modules/signals/overview.md).
- **Which AI models?** Ensemble of XGBoost, LightGBM, and CatBoost
  (voting), with a scikit-learn trio (RandomForest + GBM + LogReg) as
  fallback if the boosters aren't installed. A separate PyTorch LSTM
  predicts tomorrow's price. See [ML](modules/ml/overview.md).
- **How do you avoid cheating in ML?** Train on the first 80% of
  history, test on the last 20%, never shuffled. Walk-forward
  validation re-trains the model on a rolling window.
- **What is SHAP and why is it useful?** SHAP (SHapley Additive
  exPlanations) attributes each prediction to its input features. The
  tree-based models use `TreeExplainer`; the output tells the user
  "the model predicts UP because RSI was low, MACD was positive, and
  the price was above the 50-day average." See
  [ML implementation](modules/ml/implementation.md).
- **What is walk-forward validation?** A rolling-window evaluation:
  train on days 1–N, test on day N+1, then train on days 1–N+1, test
  on day N+2, etc. The test set is always ahead of the train set, so
  no future peeking.
- **What's the accuracy of the ML model?** It varies by stock and
  market regime. The model exposes its win rate on the test fold as
  the "accuracy" field. Don't expect 70%+.
- **Why an LSTM if the ensemble already predicts?** The ensemble
  predicts direction (UP / DOWN) for the next day. The LSTM predicts
  the actual next-day price. They're complementary.

## Backtesting

- **What is backtesting?** Running a trading rule against historical
  data. The strategy is applied to each historical day, and the
  portfolio is updated. The result is a sequence of trades, an
  equity curve, and summary metrics.
- **How do you prevent peeking at the future?** Signals use today's
  close and trade at tomorrow's open. The portfolio is updated at
  the next bar, not the current one. See
  [Backtesting implementation](modules/backtesting/implementation.md).
- **What metrics are reported?** Total return, CAGR, Sharpe ratio,
  Sortino ratio, max drawdown, win rate, profit factor, average
  trade, total trades, exposure time. Plus an equity curve chart
  and a monthly returns heatmap.
- **What strategies are available?** SMA Cross, EMA Cross, RSI
  (overbought/oversold), MACD, Bollinger Bands, and Donchian
  Channels. Each has 2–4 parameters the user can tune.

## Security

- **How does login work?** Passwords are stored only as Argon2
  hashes. On login, the server verifies the hash, creates a JWT
  access token (15 min) and a refresh token (7 day), and sets both
  as `HttpOnly`, `SameSite=Lax`, `Secure` cookies. The refresh token
  rotates on every use.
- **Why Argon2 over bcrypt?** Argon2 is the modern winner of the
  Password Hashing Competition. It's memory-hard, which makes
  GPU-based attacks expensive. Bcrypt is CPU-hard but not
  memory-hard.
- **What's the difference between access and refresh tokens?** The
  access token is short-lived (15 min) and sent with every API
  request. The refresh token is long-lived (7 days), stored in the
  database as a SHA-256 hash, and only used to mint new access
  tokens. The browser never sees the refresh token's hash.
- **What happens if my access token expires?** The api client on
  the frontend catches the 401, fires a single-flight POST to
  `/auth/refresh`, gets a new access token (and a rotated refresh
  token), and retries the original request. The user never sees
  the 401.
- **How are passwords validated?** Min 8 characters, must contain
  uppercase + lowercase + digit. The validation is on the frontend
  (Zod) and the backend (Pydantic).

## Database

- **Why PostgreSQL instead of SQLite?** Multiple users at once, data
  survives restarts, schema changes are versioned. See
  [Database](database.md).
- **What tables exist?** `users`, `refresh_tokens`, `watchlist_items`
  (live), plus `paper_portfolios`, `paper_orders`, `paper_positions`,
  `alerts`, `ml_jobs` (planned). See [Database](database.md) for
  the full schema.
- **How do you version the schema?** Alembic migrations. Every
  schema change is a Python file in `backend/alembic/versions/` with
  upgrade and downgrade paths.
- **What's the connection pooling config?** `pool_size=10`,
  `max_overflow=20`, `pool_pre_ping=True`. Handles ~30 concurrent
  requests.
- **What if PostgreSQL is down?** The backend won't start (the auth
  module requires a DB on startup). All authenticated endpoints will
  500. Public endpoints (instruments search, market-data quote)
  will still work since they don't touch the DB.

## Caching

- **What is Redis for?** Short-term cache for upstream responses:
  60s for quotes, 300s for FII/DII, 900s for sentiment, 15 minutes
  for ML results. Also used for rate limit counters.
- **What happens if Redis is down?** The backend's `core/cache.py`
  catches `RedisError` and falls through to the upstream call. The
  request still works, but it's slower (no cache hits).
- **What about the in-memory cache?** The `instrument_master.json`
  is loaded once with `@lru_cache` and kept forever. It's 646
  instruments — small enough to fit in memory.

## Edge cases

- **Why are the NSE option chains sometimes empty?** NSE rate-limits
  aggressively, and the data is only available during market hours
  (9:00–15:30 IST). Outside market hours, the response is empty.
- **Why does the first ML predict take a minute?** The model trains
  on first call per symbol. Subsequent calls hit the in-memory
  cache.
- **Why did my alert fire immediately?** The `lastPrice` vs `price`
  bug in `alerts/service.py:90` causes every alert to fire on the
  next polling cycle. The fix is a 4-line change documented in
  [Alerts implementation](modules/alerts/implementation.md#the-fix-in-detail).
- **What happens if I lose my refresh token?** Log in again. The
  old refresh token is still in the database (until 7 days) but
  cannot be used because we can't read it from the cookie. The new
  login creates a new refresh token and invalidates the chain
  (we mark all old refresh tokens for the user as revoked).
- **Can I deploy this for real money trading?** No. The verdict is
  a model output, not a recommendation. Real trading needs a paid
  data source, a regulated broker, and proper risk management.

## Code quality

- **What tests are there?** Unit tests for the service layer
  (`backend/tests/`), API tests for the routers, and snapshot
  tests for the frontend. CI runs all of them.
- **What about type checking?** `mypy` on the backend, TypeScript on
  the frontend. The frontend builds fail on type errors.
- **How is the code organised?** One module per concern on the
  backend, one folder per page on the frontend. Cross-module
  dependencies are explicit.
- **What's the linter setup?** `ruff` on the backend, `eslint` on
  the frontend. Pre-commit runs both on staged files.

## Closing

- **What did you learn from this project?** Common answers: how to
  structure a large React app, the realities of working with
  free-tier data sources, the importance of caching, the limits of
  ML in finance, the value of good docs.
- **What would you do next?** Common answers: move alerts to a
  push-notification system, add a real broker integration, deploy
  the ML models as a separate microservice, add user preferences,
  add a portfolio-sharing feature.

## Related

- [Architecture](architecture.md) — the bigger picture.
- [Demo guide](demo-guide.md) — the 7-minute walkthrough.
- [Glossary](glossary.md) — any term an examiner might use.
- [Database](database.md) — the schema, the migrations.
- [Setup](setup.md) — how to run it.