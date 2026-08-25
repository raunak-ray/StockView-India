# StockView India — Backend (FastAPI)

FastAPI modular-monolith serving the StockView India trading terminal. Python 3.12+, async-first, SQLite (dev) / PostgreSQL (prod).

---

## Prerequisites

| | Linux (Ubuntu/Debian) | macOS | Windows (PowerShell) |
|---|---|---|---|
| **Python** | `sudo apt install python3.12 python3.12-venv python3-pip` | `brew install python@3.12` | Download from [python.org](https://python.org/downloads/) — check "Add to PATH" |
| **pip** | Comes with `python3-pip` | Comes with Homebrew Python | Comes with installer |
| **Redis** (optional) | `sudo apt install redis-server && sudo systemctl start redis` | `brew install redis && brew services start redis` | Download from [redis.io](https://redis.io/download/) or use Docker |

> **Windows note:** Use PowerShell, not CMD. All commands below work identically on all three platforms — just activate the venv differently.

---

## 1. Clone & enter

```bash
git clone <repo-url>
cd StockView
```

## 2. Create virtual environment

**Linux / macOS:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> If you see `Activation failed` on Windows, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## 3. Install dependencies

**Core (always required):**
```bash
pip install -e .
```

**ML-heavy extras** — enables XGBoost/LightGBM/CatBoost ensemble, price LSTM (PyTorch), FinBERT sentiment, SHAP explanations:
```bash
pip install -e ".[ml-heavy]"
```

**Dev tools** — pytest, ruff linter, mypy type checker:
```bash
pip install -e ".[dev]"
```

**All at once:**
```bash
pip install -e ".[ml-heavy,dev]"
```

## 4. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/healthz

The API auto-creates `stockview.db` (SQLite) on first run.

## 5. Run tests

```bash
python -m pytest tests/ -v
```

All tests are offline-safe (no external API calls). Expected: **83+ tests green**.

## 6. Lint & type check

```bash
ruff check app tests        # linter
mypy app                    # type checker
```

---

## Project structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory + router mounting
│   ├── core/                    # config, security, deps, Redis, DB
│   └── modules/
│       ├── auth/                # register / login / JWT refresh
│       ├── market_data/         # Yahoo Finance history/quote/info
│       ├── instruments/         # Symbol search
│       ├── analytics/           # Technical indicators + S/R
│       ├── signals/             # Signal fusion engine
│       ├── smc/                 # Smart-money concepts (zones + fibs)
│       ├── sentiment/           # FinBERT + keyword news sentiment
│       ├── ml/                  # XGB/LGB/CAT ensemble + price LSTM
│       ├── backtesting/         # 6-strategy backtest engine
│       ├── alerts/              # Price alerts (CRUD + check-on-request)
│       ├── portfolio/           # Watchlist + paper trading
│       └── nse/                 # NSE India options/FII-DII
├── tests/                       # 83+ offline tests
├── docs/                        # Per-module docs (< 200 words each)
├── scripts/                     # Seed scripts, utilities
├── pyproject.toml               # Dependencies + tool config
└── docker-compose.yml           # API + Redis (dev)
```

---

## Optional services

| Service | Used for | Setup |
|---------|----------|-------|
| **Redis** | Caching market data, rate limiting | `redis-server` or Docker: `docker run -d -p 6379:6379 redis:7` |
| **PostgreSQL** | Production database (replaces SQLite) | Set `DATABASE_URL` in environment |

## Environment variables

Set via `.env` file in `backend/` or export directly:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./stockview.db` | Database connection string |
| `REDIS_URL` | `redis://localhost:6379` | Redis cache URL |
| `JWT_SECRET` | (auto-generated) | Secret for signing JWT tokens |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins |

---

## API modules at a glance

| Module | Prefix | What it does |
|--------|--------|-------------|
| auth | `/api/v1/auth` | Register, login, refresh, logout |
| market_data | `/api/v1/market-data` | History, quote, info, movers |
| instruments | `/api/v1/instruments` | Symbol search |
| analytics | `/api/v1/analytics` | Indicators, support/resistance |
| signals | `/api/v1/signals` | Fusion engine (tech + ML + news) |
| smc | `/api/v1/smc` | Smart-money zones + Fibonacci |
| sentiment | `/api/v1/sentiment` | News headlines, sentiment score |
| ml | `/api/v1/ml` | Predict (background job), capabilities |
| backtesting | `/api/v1/backtesting` | Run backtest, list strategies |
| alerts | `/api/v1/alerts` | Price alerts CRUD |
| portfolio | `/api/v1/portfolio` | Watchlist + paper trading |
| nse | `/api/v1/nse` | NSE quote chain, options, FII/DII |
