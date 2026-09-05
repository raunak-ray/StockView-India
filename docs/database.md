# Database

StockView uses **PostgreSQL 16** for persistent state. Connection
string: `postgresql+asyncpg://postgres:postgres@localhost:5432/stockview`
(set via the `SV_DATABASE_URL` env var; defaults to a local Docker
instance — see [Setup](setup.md)). Schema changes go through **Alembic**
migrations; never edit tables by hand.

## The tables

```mermaid
erDiagram
    users ||--o{ refresh_tokens : "has many"
    users ||--o{ watchlist_items : "has many"
    users ||--o{ paper_portfolios : "has one"
    users ||--o{ paper_orders : "has many"
    users ||--o{ alerts : "has many"
    users ||--o{ ml_jobs : "has many"
    paper_portfolios ||--o{ paper_orders : "owns"
    paper_portfolios ||--o{ paper_positions : "contains"
```

| Table | Module | Purpose | Status |
|---|---|---|---|
| `users` | auth | Account credentials + role | ✅ Live |
| `refresh_tokens` | auth | Hashed refresh tokens, rotate on use | ✅ Live |
| `watchlist_items` | portfolio | User's starred tickers | ✅ Live |
| `paper_portfolios` | portfolio | Virtual cash + per-user portfolio | 🟡 Migration pending |
| `paper_orders` | portfolio | Order history | 🟡 Migration pending |
| `paper_positions` | portfolio | Open positions (avg cost, LTP) | 🟡 Migration pending |
| `alerts` | alerts | Price alarm definitions | 🟡 Migration pending |
| `ml_jobs` | ml | Background training job registry | 🟡 Migration pending |

The "🟡 Migration pending" tables are currently held in **in-process
memory** dicts (e.g. `_paper_portfolios: dict[str, dict]`). The
SQLAlchemy models and Alembic migration scripts are written but not
yet applied. A server restart wipes the in-memory data; concurrent
users could collide. See `plan/todo.md` for the migration plan.

## Table details

### `users` (`backend/app/modules/auth/models.py`)

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `String(36)` | PK | UUID v4 |
| `username` | `String(50)` | UNIQUE, INDEX | Min 3 chars, regex `^[a-zA-Z0-9_]+$` |
| `password_hash` | `String(255)` | NOT NULL | Argon2 hash (never plain) |
| `role` | `String(20)` | DEFAULT `"user"` | Today: always `"user"`. Future: `"admin"`. |
| `created_at` | `DateTime(timezone=True)` | server_default=now() | Account creation time |

The User type on the frontend (`frontend/lib/api/auth.ts`) mirrors
this — except `password_hash` is **never** sent to the client.

### `refresh_tokens` (`backend/app/modules/auth/models.py`)

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `String(36)` | PK | UUID v4 |
| `user_id` | `String(36)` | FK → `users.id`, ON DELETE CASCADE, INDEX | |
| `token_hash` | `String(64)` | UNIQUE, INDEX | SHA-256 hash of the actual token. The token itself is in the cookie. |
| `expires_at` | `DateTime(timezone=True)` | NOT NULL | 7 days from issue |
| `revoked_at` | `DateTime(timezone=True)` | NULL | Set on rotation or logout |
| `created_at` | `DateTime(timezone=True)` | server_default=now() | |

The `is_expired` property is a Python-side check (not a DB constraint)
that compares `expires_at` to the current UTC time. A token is
**revoked** when `revoked_at IS NOT NULL` (rotation) or **expired**
when `expires_at < now`. Either way, the token is rejected.

### `watchlist_items` (`backend/app/modules/portfolio/models.py`)

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `String(36)` | PK | UUID v4 |
| `user_id` | `String(36)` | FK → `users.id`, ON DELETE CASCADE, INDEX | |
| `ticker` | `String(32)` | INDEX | Full ticker e.g. `RELIANCE.NS` |
| `sort_order` | `Integer` | DEFAULT 0 | Manual sort order (currently always 0) |
| `created_at` | `DateTime(timezone=True)` | default=now() | When the user starred this ticker |

**Unique constraint**: `UNIQUE(user_id, ticker)` — a user cannot
star the same ticker twice. The duplicate insert raises
`IntegrityError` which the API surfaces as a 400.

### `paper_portfolios` 🟡 (planned)

| Column | Type | Notes |
|---|---|---|
| `id` | `String(36)` | PK |
| `user_id` | `String(36)` | FK → `users.id`, UNIQUE (one portfolio per user) |
| `cash` | `Numeric(14, 2)` | Available cash in ₹ |
| `initial_cash` | `Numeric(14, 2)` | ₹1,00,000 (for P&L reporting) |
| `created_at` | `DateTime(timezone=True)` | |
| `updated_at` | `DateTime(timezone=True)` | Set on every order |

### `paper_orders` 🟡 (planned)

| Column | Type | Notes |
|---|---|---|
| `id` | `String(36)` | PK |
| `user_id` | `String(36)` | FK → `users.id`, INDEX |
| `portfolio_id` | `String(36)` | FK → `paper_portfolios.id` |
| `symbol` | `String(32)` | e.g. `RELIANCE.NS` |
| `type` | `String(4)` | `"BUY"` or `"SELL"` |
| `qty` | `Integer` | Positive integer |
| `price` | `Numeric(14, 2)` | Fill price |
| `value` | `Numeric(14, 2)` | `qty * price` (denormalised for query speed) |
| `mode` | `String(10)` | Always `"paper"` |
| `ts` | `DateTime(timezone=True)` | When the order was placed |

### `paper_positions` 🟡 (planned)

| Column | Type | Notes |
|---|---|---|
| `id` | `String(36)` | PK |
| `portfolio_id` | `String(36)` | FK → `paper_portfolios.id` |
| `symbol` | `String(32)` | UNIQUE within the portfolio |
| `qty` | `Integer` | Shares held |
| `avg_cost` | `Numeric(14, 2)` | Weighted average (BUYs add, SELLs reduce) |
| `ltp` | `Numeric(14, 2)` | Last traded price, refreshed on query |
| `created_at` | `DateTime(timezone=True)` | |
| `updated_at` | `DateTime(timezone=True)` | |

### `alerts` 🟡 (planned)

| Column | Type | Notes |
|---|---|---|
| `id` | `String(36)` | PK |
| `user_id` | `String(36)` | FK → `users.id`, INDEX |
| `symbol` | `String(32)` | e.g. `RELIANCE.NS` |
| `price` | `Numeric(14, 2)` | Threshold |
| `condition` | `String(10)` | `"above"` or `"below"` |
| `label` | `String(50)` | Human-readable e.g. `"Crosses Above"` |
| `created` | `DateTime(timezone=True)` | When the alert was created |
| `triggered` | `Boolean` | DEFAULT false — set true by the polling loop |
| `triggered_at` | `DateTime(timezone=True)` | NULL until triggered |

**Unique constraint**: `UNIQUE(user_id, symbol, price, condition)` —
prevents duplicate alerts (a user cannot set two "RELIANCE above
2800" alerts).

### `ml_jobs` 🟡 (planned)

| Column | Type | Notes |
|---|---|---|
| `id` | `String(36)` | PK |
| `user_id` | `String(36)` | FK → `users.id` |
| `symbol` | `String(32)` | The stock being trained on |
| `model` | `String(20)` | `"ensemble"` or `"lstm"` |
| `status` | `String(20)` | `"queued"` / `"running"` / `"done"` / `"failed"` |
| `progress` | `Integer` | 0–100 |
| `result_id` | `String(36)` | FK to the prediction table (when status=done) |
| `error` | `String(500)` | NULL unless status=failed |
| `started_at` | `DateTime(timezone=True)` | |
| `finished_at` | `DateTime(timezone=True)` | NULL until done |

Today, ML training runs in-process via `asyncio.create_task`. The
status is exposed through a query param on the predict endpoint
(`?job_id=...`). The DB-backed job registry is part of the
migration.

## Why PostgreSQL (not SQLite)

The project previously defaulted to SQLite (`stockview.db`, a single
file). It worked for a single user on a single machine, but broke
when:

- **Concurrent access**: SQLite locks the entire DB on write. Two
  simultaneous order placements would serialise or error.
- **State persistence**: paper trades, alerts, and ML jobs were held
  in `dict[str, …]` in process memory. A server restart wiped
  everything.
- **Schema versioning**: ad-hoc DDL changes were made by hand. No
  audit trail. No rollback.

PostgreSQL fixes all three. Connection is via the async driver
`asyncpg`, so the same `AsyncSession` API works whether the backing
DB is SQLite (dev) or PostgreSQL (prod).

## Migrations

Schema changes go through Alembic. The setup:

```bash
cd backend
alembic upgrade head         # apply all migrations
alembic downgrade -1         # roll back one migration
alembic revision --autogenerate -m "add ml_jobs table"
```

The Alembic config lives in `backend/alembic.ini` and the version
scripts in `backend/alembic/versions/`. The migration history tracks
every schema change with a timestamp, a description, and both upgrade
and downgrade paths.

The autogenerate workflow compares the live DB to the SQLAlchemy
models declared in `backend/app/modules/*/models.py` and produces the
diff. Always review the generated migration before committing — it
sometimes misses indexes or constraint changes.

## The session lifecycle

```python
# backend/app/core/deps.py
async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
```

Every request that needs DB access gets a fresh `AsyncSession` via the
`get_db` dependency. The session is closed when the request ends (or
on exception).

Module code uses `await db.execute(select(User).where(...))` and
similar — see `backend/app/modules/auth/service.py` for the canonical
pattern.

## Connection pooling

The async engine is configured with:

- `pool_size=10` — 10 persistent connections.
- `max_overflow=20` — up to 20 additional connections under load.
- `pool_pre_ping=True` — verify connection health before use (handles
  idle disconnects).

This handles ~30 concurrent requests with no contention. For higher
loads, scale the connection pool or use a connection pooler like
PgBouncer.

## Backup and recovery

For production:

1. **Logical backups**: `pg_dump --format=custom stockview > backup.dump`
   (run nightly via cron).
2. **Point-in-time recovery**: enable WAL archiving and configure
   `archive_mode=on` + `archive_command`.
3. **Restore**: `pg_restore --dbname=stockview backup.dump` or
   `pg_restore --clean --if-exists --dbname=stockview backup.dump`.

For development, the Docker volume `postgres-data` can be snapshotted
via `docker volume create --name stockview-pg-snapshot` and a manual
`docker run --rm -v stockview-pg-snapshot:/from -v stockview-pg:/to
alpine cp -a /from/. /to/`.

## What's NOT in the database

Some things are intentionally **not** persisted:

- **In-process cache** (`@lru_cache` on the instruments JSON). It is
  loaded from `backend/app/modules/instruments/data/instrument_master.json`
  on first call and kept forever. No DB roundtrip.
- **ML model weights** (xgb.pkl, lstm.pt). Today these are
  serialised to disk in a per-process temp dir. The migration to
  PostgreSQL does **not** cover model storage — for that, use
  object storage (S3, GCS) or a model registry (MLflow).
- **Background job results**. The predict endpoint trains on first
  call and caches in memory. A restart re-trains. The `ml_jobs`
  table is for **status tracking**, not for caching predictions.
- **Upstream data** (yfinance responses, NSE feeds). These go in
  Redis, not PostgreSQL. PostgreSQL is for app state, not cache.

## Related

- [Setup](setup.md) — Docker Compose, env vars, first migration.
- [Architecture](architecture.md) — the bigger picture.
- `backend/app/core/db.py` — the SQLAlchemy `Base` and engine setup.
- `backend/app/core/config.py` — env var definitions.
- `backend/app/modules/*/models.py` — per-module model declarations.