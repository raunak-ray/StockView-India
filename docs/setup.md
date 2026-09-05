# Setup

Get the app running on your machine. The happy path takes about 5
minutes if you already have Docker, Python 3.12+, and Node.js 20+
installed. The troubleshooting section below covers the 6 most common
issues.

## Prerequisites

| Tool | Minimum version | Why |
|---|---|---|
| **Python** | 3.12 | Backend runtime. Required for the async syntax and the typing. |
| **Node.js** | 20 | Frontend runtime. Required for the App Router. |
| **Docker** | 24 | Runs PostgreSQL and Redis as containers. |
| **Docker Compose** | v2 | Brought with Docker Desktop or installed separately. |
| **Git** | 2.30 | Clone the repo. |
| **4 GB RAM free** | — | PostgreSQL + Redis + Node dev server + ML training on demand. |

On macOS with Homebrew: `brew install python@3.12 node docker docker-compose git`.
On Ubuntu: `sudo apt install python3.12 python3.12-venv nodejs npm docker.io docker-compose-plugin git`.
On Windows: use WSL2 for the backend; the frontend runs natively.

## First-time setup

### 1. Clone and start the data services

```bash
git clone <repo-url> StockView
cd StockView/backend
docker compose up -d postgres redis
```

Expected output: `Container stockview-postgres  Started` and
`Container stockview-redis  Started`. The first run pulls the
PostgreSQL 16 and Redis 7 images (~400 MB total).

Verify they're up:

```bash
docker compose ps
# NAME                  STATUS              PORTS
# stockview-postgres    Up (healthy)        0.0.0.0:5432->5432/tcp
# stockview-redis       Up (healthy)        0.0.0.0:6379->6379/tcp
```

If `STATUS` is not "healthy" within 10s, see the
[troubleshooting](#troubleshooting) section below.

### 2. Backend

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

The `pip install -e ".[dev]"` pulls FastAPI, SQLAlchemy (async),
asyncpg, redis, yfinance, ta, optional torch/transformers (for
FinBERT + LSTM), pytest, ruff, mypy, and the dev-only deps.

The `alembic upgrade head` creates the `users`, `refresh_tokens`,
and `watchlist_items` tables in PostgreSQL. If you see
"relation already exists" errors, see [below](#alembic-says-relation-already-exists).

The `uvicorn` line starts the dev server with hot reload on
`http://localhost:8000`. You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

The auto-generated API docs are at `http://localhost:8000/docs`
(Swagger UI) and `http://localhost:8000/redoc` (ReDoc).

### 3. Frontend

In a second terminal:

```bash
cd ../frontend
npm install
npm run dev
```

Expected output: `Local: http://localhost:3000/`. Open the URL in a
browser. You should see the landing page with a "Get started" button
and a sign-in / register link.

### 4. First login

The app ships with a seeded `demo` user. Open the sign-in page and
log in as:

- **Username**: `demo`
- **Password**: `demo123`

You should land on the dashboard at `/app`. The "Indian Indices"
cards should show Nifty, Sensex, and Bank Nifty within ~1 second (the
quotes are cached for 60 seconds after the first request).

### 5. Optional: seed extra data

The seed script in `backend/scripts/seed.py` creates a few extra demo
users with realistic watchlists. Run it once:

```bash
cd backend
python scripts/seed.py
```

This is **not** required for the app to work. The default `demo`
user is created automatically on first run.

## Environment variables

All env vars are read by `backend/app/core/config.py` via
`pydantic-settings`. The defaults are in `.env.example`. Override
per-environment by editing `.env` (gitignored) or by exporting in the
shell.

| Var | Default | What |
|---|---|---|
| `SV_DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/stockview` | PostgreSQL DSN |
| `SV_REDIS_URL` | `redis://localhost:6379/0` | Redis DSN |
| `SV_JWT_SECRET` | (required) | HS256 signing key. **Generate a random 32-byte string in production.** |
| `SV_JWT_ALGORITHM` | `HS256` | The JWT signing algorithm. |
| `SV_ACCESS_TOKEN_TTL` | `900` (15 min) | Access token lifetime in seconds |
| `SV_REFRESH_TOKEN_TTL` | `604800` (7 days) | Refresh token lifetime in seconds |
| `SV_ENV` | `dev` | One of `dev`, `prod`. Affects CORS, rate limits, doc exposure. |
| `SV_LOG_LEVEL` | `INFO` | `DEBUG` for verbose logs. |
| `SV_RATE_LIMIT_LOGIN` | `10/minute` | Per-IP login attempts |
| `SV_RATE_LIMIT_DEFAULT` | `60/minute` | Per-IP default limit |
| `SV_ENABLE_FINBERT` | `false` | Set to `true` to load the FinBERT model (slower first call, ~500MB RAM). |
| `SV_ENABLE_LSTM` | `true` | Set to `false` to skip the optional LSTM path. |

The frontend reads only **public** env vars (prefixed `NEXT_PUBLIC_`):

| Var | Default | What |
|---|---|---|
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000/api/v1` | Backend API root |
| `NEXT_PUBLIC_DEFAULT_THEME` | `dark` | `light` or `dark` |

## Quality checks

Run these before committing:

```bash
# Backend
cd backend
python -m pytest tests/ -v
ruff check app tests
mypy app
```

```bash
# Frontend
cd frontend
npm run lint
npm run build
```

CI runs the same checks. A red CI means at least one of these is
failing.

## Pre-commit

The repo ships with a pre-commit config at `.pre-commit-config.yaml`.
After cloning, run:

```bash
pre-commit install
```

This installs a Git hook that runs ruff + eslint on staged files.
Commits are blocked if checks fail.

## Production checklist

For a deployment (not the demo):

- [ ] `SV_JWT_SECRET` is a random 32+ byte secret, **not** the dev value.
- [ ] `SV_ENV=prod` to disable docs and tighten CORS.
- [ ] PostgreSQL is on a separate machine or managed service (RDS, Cloud SQL).
- [ ] Redis is on a separate machine or managed service (ElastiCache, Memorystore).
- [ ] HTTPS terminated at a load balancer; cookies are `Secure` + `SameSite=Lax`.
- [ ] Logs shipped to a centralised store (CloudWatch, Loki, Datadog).
- [ ] Backups: nightly `pg_dump` to S3, WAL archiving enabled.
- [ ] Rate limits tuned: `SV_RATE_LIMIT_LOGIN=5/minute`,
      `SV_RATE_LIMIT_DEFAULT=120/minute`.
- [ ] Health check: `GET /healthz` returns 200 when the service is ready.
- [ ] Monitoring: alert on 5xx rate > 1% over 5 minutes, p95 latency > 2s, Redis down, DB connection errors.

## Troubleshooting

### Postgres won't start: "port 5432 already in use"

You have a local PostgreSQL running. Either:

- **Stop your local one**: `sudo systemctl stop postgresql` (Linux),
  or stop the brew service (`brew services stop postgresql@16` on
  Mac), or stop the Mac Postgres app.
- **Use a different port**: edit `docker-compose.yml` to map
  `5433:5432`, then set `SV_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/stockview`.

### Redis won't start: "port 6379 already in use"

Same as above. Either stop your local Redis or map a different port.

### Alembic says "relation already exists"

The DB has tables from a previous run but Alembic doesn't know. Two
options:

- **Drop the DB and re-create**:
  ```bash
  docker compose down -v
  docker compose up -d postgres redis
  alembic upgrade head
  ```
  The `-v` removes the volume, which deletes the old data.

- **Stamp the head**:
  ```bash
  alembic stamp head
  ```
  This marks the existing tables as up-to-date without re-creating
  them. Use this only if you're sure the schema is correct.

### yfinance returns 429 (Too Many Requests)

Yahoo Finance rate-limits aggressive callers. The backend's
5-tier cache mitigates this in normal use, but a fresh start with
many concurrent requests can hit the limit.

- Wait 10 minutes and try again.
- Reduce concurrency by closing other yfinance clients on your
  machine.
- For production, run a single backend instance (vertical scale) or
  add a request-coalescing layer.

### NSE endpoints fail with 502 / 403

NSE India blocks some non-India IPs. From outside India, NSE
endpoints will fail. The backend has multi-layer fallbacks
(Trendlyne, static fixtures) so the request returns **something**,
but for full functionality, test from an India-based network or
use a VPN.

### First ML predict takes 30–60 seconds

The ML module trains the model on first call (per symbol, per process
lifetime). Subsequent calls hit the in-memory cache and return in
~50ms. This is expected — see `docs/modules/ml/overview.md`.

If you want pre-warmed models on startup, set up a warmup script
(not bundled today).

### Alerts fire immediately after creation

The `lastPrice` vs `price` bug in `backend/app/modules/alerts/service.py`
makes every active alert fire on the next polling cycle (within 30s).
The fix is a 4-line change documented in `docs/modules/alerts/implementation.md`.
Until the fix is applied, every alert you create will move to
"Triggered" almost instantly.

### Frontend shows "Failed to fetch"

The backend is not reachable. Check:

1. Is `uvicorn` running? (Check the terminal where you started it.)
2. Is `NEXT_PUBLIC_API_BASE` correct? (Default: `http://localhost:8000/api/v1`.)
3. CORS: in dev, the backend allows `http://localhost:3000` by
   default. If your frontend runs on a different port, update
   `SV_CORS_ORIGINS` (a comma-separated list).

### Curl test for the backend

Quick check that the API is alive:

```bash
curl http://localhost:8000/healthz
# {"status":"ok"}

curl http://localhost:8000/api/v1/instruments/search?q=reliance
# {"results":[{"ticker":"RELIANCE.NS","name":"Reliance Industries Limited",...}]}
```

If these return correctly, the backend is healthy and the issue is on
the frontend.

## Daily workflow

```bash
# Start everything
cd StockView
docker compose up -d postgres redis
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000 &
cd ../frontend && npm run dev
```

```bash
# Stop everything
docker compose down
# Kill the uvicorn and node processes (Ctrl+C in their terminals)
```

```bash
# Wipe and re-start
docker compose down -v
docker compose up -d postgres redis
cd backend && alembic upgrade head
```

## Related

- [Database](database.md) — schema details, migrations, what is and isn't persisted.
- [Architecture](architecture.md) — the bigger picture.
- [Glossary](glossary.md) — terms used throughout the docs.
- [Demo guide](demo-guide.md) — the 7-minute walkthrough for examiners.