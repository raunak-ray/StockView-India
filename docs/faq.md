# FAQ

Common questions beyond the [viva list](viva-questions.md). Grouped
by topic. Each answer is short — see the linked doc for full
detail.

## Daily use

- **Why are the NSE option chains sometimes empty?** NSE rate-limits
  aggressively, and the data is only available during market hours
  (9:00–15:30 IST). Outside market hours, the response is empty.
  See the [NSE module](modules/nse/overview.md).
- **Why is the NSE breadth tab grey / showing a 502?** NSE blocks
  some non-India IPs. The backend tries Trendlyne as a fallback,
  then a static fixture. If both fail, you see the error.
- **Why does the first ML predict take a minute?** The model trains
  on first call per symbol. Subsequent calls hit the in-memory
  cache and return in ~50ms. See the [ML module](modules/ml/overview.md).
- **Why did my alert fire immediately?** The `lastPrice` vs `price`
  bug — known issue, 4-line fix documented in
  [Alerts implementation](modules/alerts/implementation.md#the-fix-in-detail).
- **Can I add a custom indicator?** Not from the UI. The indicator
  set is fixed (RSI, MACD, BB, ATR, SMA, EMA). To add a new one,
  edit `backend/app/modules/analytics/service.py` and add a
  corresponding field to the API response.
- **Can I get intraday data?** No. The free tier of yfinance
  provides daily data only. Intraday requires a paid data source.
- **What time zone are the timestamps in?** The backend stores UTC.
  The frontend formats in the browser's local time zone. The
  default in dev is IST (UTC+5:30).

## Account and security

- **I forgot my password.** There is no password reset flow today.
  The seeded `demo` user is always available with `demo123`.
  Outside the demo, recreate the user manually in the DB.
- **Can I delete my account?** No. Account deletion is not
  implemented.
- **How do I log out?** Click your avatar in the topbar →
  "Sign out". The refresh token is revoked in the database.
- **Can I have multiple sessions?** Yes. Each session has its own
  refresh token. The user can have N active sessions at once.
- **What's the rate limit on login?** 10 attempts per minute per
  IP. Exceeding it returns 429. The limit is per-IP, not per-user.

## Trading and paper trading

- **How much virtual cash do I start with?** ₹1,00,000. The amount
  is fixed; there's no "top-up" feature.
- **Is the order price the live price?** Yes — the price you
  entered. There's no "market order" vs "limit order" distinction
  in paper trading; every order fills at the entered price.
- **Can I short a stock?** No. Only buy and sell of held positions.
- **What happens to my positions on server restart?** They are
  lost. The paper-trading store is in-memory today; the
  PostgreSQL migration will fix this. See
  [Database](database.md#paper_portfolios--planned).
- **Can I export my paper trade history?** No, not from the UI.
  The orders are queryable via the API at
  `GET /api/v1/paper/orders`.

## ML and backtesting

- **Can I train a model on a custom date range?** Not from the UI.
  The default is 5 years. To change it, edit the `lookback_years`
  constant in `backend/app/modules/ml/features.py`.
- **Can I use the model for real trading?** No. The model is for
  education. Real trading needs a paid data source, a regulated
  broker, and proper risk management.
- **What's the difference between the ensemble and the LSTM?** The
  ensemble predicts direction (UP / DOWN) for tomorrow. The LSTM
  predicts the actual next-day price. They're complementary.
- **Why is the LSTM's prediction so different from the ensemble's?**
  The LSTM is more sensitive to recent volatility. In ranging
  markets, the ensemble and LSTM may disagree. The fusion
  averages them with a weight that depends on recent accuracy.
- **What's a good Sharpe ratio?** Above 1.0 is decent, above 2.0 is
  great, above 3.0 is suspicious (probably overfit). The
  backtest reports the Sharpe, but a high Sharpe on history
  doesn't guarantee future returns.
- **Why does my backtest show 0 trades?** The strategy didn't find
  any entry signals. Check the parameters (e.g. RSI period too
  long, MA too slow). Try the default parameters first.

## API and integration

- **Where are the API docs?** `http://localhost:8000/docs` (Swagger
  UI) and `http://localhost:8000/redoc` (ReDoc). Auto-generated
  from the OpenAPI schema.
- **Can I use the API from a script?** Yes — the auth is via
  httpOnly cookies, so a script needs to handle the login +
  refresh flow. The simplest path is to use the
  `api/v1/auth/login` endpoint to get the cookies, then send
  them with every request.
- **Is there a rate limit on the API?** Yes — 60/minute on default
  endpoints, 10/minute on login. Returns 429 when exceeded.
- **Is the API CORS-enabled for any origin?** No — only
  `http://localhost:3000` in dev. Configure `SV_CORS_ORIGINS` in
  prod to allow your frontend's origin.

## Deployment

- **Can I deploy this for production?** Yes, but the in-memory
  stores (alerts, paper trading) will lose data on restart.
  Migrate to PostgreSQL first (see `plan/todo.md` Phase A) and
  set `SV_JWT_SECRET` to a strong random value.
- **What about HTTPS?** The backend is HTTP-only. Terminate TLS at
  a load balancer (nginx, Caddy, AWS ALB) and set the
  `SV_BEHIND_PROXY=true` env var so the cookies are flagged
  `Secure`.
- **Can I run multiple backend instances behind a load balancer?**
  Yes, but the in-memory stores will diverge between instances.
  Use PostgreSQL for shared state.

## Contributing

- **How do I add a new module?** See the per-module structure in
  [modules/README.md](modules/README.md). The 3-file pattern is
  required for all new modules.
- **How do I add a new page?** Same pattern in
  [pages/README.md](pages/README.md). The page route is the folder
  name; the components live in the same folder.
- **How do I report a bug?** File an issue on the repo. Include:
  what you did, what you expected, what happened, and the
  relevant log output.