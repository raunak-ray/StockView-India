# StockView India

Full-stack Indian stock trading terminal — FastAPI backend + Next.js frontend.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.12%2B-green)
![Node](https://img.shields.io/badge/node-18%2B-green)
![Tests](https://img.shields.io/badge/tests-83%2B-brightgreen)

---

## Demo

> **Add your own screenshots and video below.** Place images in `docs/screenshots/` and reference them here.

```
docs/screenshots/
├── dashboard.png          # Market overview + movers
├── stock-terminal.png     # Chart + analytics + ML
├── fusion-verdict.png     # Signal fusion card
├── backtest.png           # Strategy results + equity curve
├── paper-trading.png      # Virtual portfolio
├── markets.png            # NSE options + FII/DII
├── sectors.png            # Sector treemap
└── demo.mp4               # Full walkthrough video
```

### Screenshots

| Dashboard | Stock Terminal | Signal Fusion |
|-----------|---------------|---------------|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Terminal](docs/screenshots/stock-terminal.png) | ![Fusion](docs/screenshots/fusion-verdict.png) |

| Backtesting | Paper Trading | Markets |
|------------|--------------|---------|
| ![Backtest](docs/screenshots/backtest.png) | ![Paper](docs/screenshots/paper-trading.png) | ![Markets](docs/screenshots/markets.png) |

### Demo video

[![Watch the demo](docs/screenshots/demo.mp4)](docs/screenshots/demo.mp4)

---

## What it does

A complete Indian stock analysis terminal — originally built in Streamlit (8,700 lines), now rewritten as a production-grade modular monolith.

### Features

| Feature | Description |
|---------|-------------|
| **Live Charts** | TradingView-style candlestick charts with SMA/EMA/BB/RSI/MACD overlays |
| **Technical Analytics** | 15+ indicators, support/resistance zones, Fibonacci levels |
| **Signal Fusion** | Blends technical (45%) + ML (40%) + news sentiment (15%) into one verdict |
| **ML Predictions** | XGBoost/LightGBM/CatBoost ensemble + price LSTM, background training |
| **Smart Money Concepts** | Order blocks, fair value gaps, liquidity zones |
| **News & Sentiment** | FinBERT + keyword scoring, mood meters |
| **NSE India Data** | Option chain, PCR, max pain, FII/DII flows |
| **Backtesting** | 6 strategies, look-ahead-free engine, equity curve + trade log |
| **Paper Trading** | Virtual ₹1L portfolio with live P&L |
| **Price Alerts** | Set above/below alerts, checked on page load |
| **Sector Treemap** | Visual Nifty sector heatmap with drill-down |
| **Compare** | Side-by-side two-symbol comparison |

---

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

API runs at http://localhost:8000 — Swagger docs at http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at http://localhost:3000

> **ML features** require optional extras: `pip install -e ".[ml-heavy]"` in the backend.

See [`backend/README.md`](backend/README.md) and [`frontend/README.md`](frontend/README.md) for full setup on Linux, macOS, and Windows.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       Frontend (Next.js)                      │
│  React 19 · Tailwind · React Query · lightweight-charts       │
├──────────────────────────────────────────────────────────────┤
│                       Backend (FastAPI)                        │
│  Modular monolith — 12 modules, async, SQLite/PostgreSQL      │
├──────────┬──────────┬──────────┬──────────┬──────────────────┤
│  Auth    │ Market   │ Signals  │   ML     │  Analytics       │
│  Alerts  │   NSE    │   SMC    │ Backtest │  Sentiment       │
├──────────┴──────────┴──────────┴──────────┴──────────────────┤
│  PostgreSQL (prod) / SQLite (dev)  ·  Redis (optional cache) │
└──────────────────────────────────────────────────────────────┘
```

---

## Project structure

```
StockView/
├── backend/                # FastAPI modular monolith
│   ├── app/
│   │   ├── core/           # Config, security, DB, Redis, deps
│   │   └── modules/        # 12 feature modules (auth, ml, signals, ...)
│   ├── tests/              # 83+ offline tests
│   ├── docs/               # Per-module docs (≤200 words each)
│   └── pyproject.toml      # Python deps + tool config
├── frontend/               # Next.js 16 app
│   ├── app/                # App Router pages
│   ├── components/         # Shared UI components
│   ├── lib/                # API clients, hooks, utilities
│   └── package.json        # Node deps
├── app.py                  # Legacy Streamlit app (read-only reference)
├── plan/                   # Planning docs and phase checklists
└── README.md               # This file
```

---

## Tech stack

### Backend
- **Framework:** FastAPI (async, Pydantic v2)
- **Database:** SQLAlchemy 2 async + SQLite (dev) / PostgreSQL (prod)
- **Cache:** Redis (optional)
- **Auth:** JWT httpOnly cookies + Argon2
- **Data:** Yahoo Finance (yfinance), NSE India (nsepython)
- **ML:** XGBoost, LightGBM, CatBoost, PyTorch (LSTM), FinBERT, SHAP
- **Testing:** pytest + pytest-asyncio, ruff, mypy

### Frontend
- **Framework:** Next.js 16 (App Router, Turbopack)
- **UI:** React 19, Tailwind CSS, Radix UI (shadcn pattern)
- **State:** React Query (TanStack Query v5)
- **Charts:** lightweight-charts (TradingView)
- **Tools:** TypeScript, ESLint

---

## Documentation

Every module has a docs folder with a short (< 200 word) overview:

| Module | Docs |
|--------|------|
| Auth | [`backend/docs/auth/`](backend/docs/auth/) |
| Market Data | [`backend/docs/market-data/`](backend/docs/market-data/) |
| Analytics | [`backend/docs/analytics/`](backend/docs/analytics/) |
| Signals | [`backend/docs/signals/`](backend/docs/signals/) |
| SMC | [`backend/docs/smc/`](backend/docs/smc/) |
| Sentiment | [`backend/docs/sentiment/`](backend/docs/sentiment/) |
| ML | [`backend/docs/ml/`](backend/docs/ml/) |
| Backtesting | [`backend/docs/backtesting/`](backend/docs/backtesting/) |
| Alerts | [`backend/docs/alerts/`](backend/docs/alerts/) |
| Portfolio | [`backend/docs/portfolio/`](backend/docs/portfolio/) |
| NSE | [`backend/docs/nse/`](backend/docs/nse/) |
| Instruments | [`backend/docs/instruments/`](backend/docs/instruments/) |

---

## Running tests

```bash
# Backend
cd backend
pip install -e ".[dev]"
python -m pytest tests/ -v

# Frontend
cd frontend
npm run lint
npm run build
```

---

## Docker (dev)

```bash
cd backend
docker-compose up -d
# Redis at localhost:6379, API at localhost:8000
```

---

## Contributing

1. Branch from `feature/signals`
2. Follow conventional commits: `feat:`, `fix:`, `test:`, `docs:` (≤30 words)
3. Backend: `pytest && ruff check app tests && mypy app`
4. Frontend: `npm run lint && npm run build`
5. Update `plan/todo.md` when completing a phase

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

> **Built as a final-year project** — migrating a monolithic Streamlit app into a production-grade modular architecture with proper separation of concerns, type safety, and 83+ offline tests.
