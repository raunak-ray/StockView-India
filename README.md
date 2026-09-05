# StockView India

Full-stack Indian stock analysis terminal — FastAPI backend + Next.js
frontend. Search any NSE stock, get a chart, indicators, news, an
ML prediction, and one BUY / HOLD / SELL verdict.

GitHub: https://github.com/raunak-ray/StockView-India

## Run it

After cloning, you need a `.env` file with the hosted database and
Redis URLs — **get it from the project lead** (don't edit the values
yourself; they point to managed services).

```bash
git clone https://github.com/raunak-ray/StockView-India
cd StockView-India
```

Drop the `.env` you got into `backend/.env`.

### Backend

```bash
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate         # macOS / Linux
pip install -e ".[dev]"
stockview-backend migrate
stockview-backend dev
```

Backend runs at http://localhost:8000.

### Frontend (new terminal)

```bash
cd frontend
cp .env.example .env       # macOS / Linux
# copy .env.example .env   # Windows PowerShell
npm install
npm run dev
```

The `frontend/.env` file tells the browser where the backend lives
(see `NEXT_PUBLIC_API_BASE` — defaults to `http://localhost:8000/api/v1`
for dev).

App runs at http://localhost:3000. Log in with `demo` / `demo123`.

## What it does

- **Live charts** — candlesticks, SMA / EMA / BB / RSI / MACD overlays
- **One-word verdict** — BUY / HOLD / SELL with the top reasons
- **ML prediction** — XGBoost / LightGBM / CatBoost ensemble + LSTM
- **News mood** — FinBERT scores recent headlines
- **Backtesting** — 6 strategies, equity curve, monthly heatmap
- **Paper trading** — virtual ₹1,00,000 portfolio
- **Price alerts** — set above / below thresholds
- **Sector treemap** — visual Nifty heatmap
- **NSE data** — option chain (PCR + max-pain), FII/DII flows

## Project structure

```
StockView-India/
├── backend/            # FastAPI modular monolith (13 modules)
│   ├── app/            # Routers, services, models
│   ├── docs/           # Per-module dev notes
│   └── pyproject.toml
├── frontend/           # Next.js 16 (12 pages)
│   ├── app/            # App Router pages
│   ├── components/     # Shared UI
│   └── lib/            # API clients, hooks
├── docs/               # Full project documentation
│   ├── setup.md        # Detailed setup guide
│   ├── architecture.md
│   ├── modules/        # 13 backend modules
│   └── pages/          # 12 frontend pages
└── plan/               # Planning + phase checklists
```

## Documentation

Start with [`docs/setup.md`](docs/setup.md) for the full setup walkthrough
(Windows / Mac / Linux, troubleshooting, env vars, daily workflow).

The full handbook is at [`docs/`](docs/README.md) — architecture
diagram, 13 backend module docs, 12 frontend page docs, database
schema, glossary, viva questions.

## Tech stack

- **Backend** — FastAPI, SQLAlchemy 2 (async), asyncpg, PostgreSQL
  (Neon), Redis (Upstash), yfinance, nsepython, XGBoost / LightGBM /
  CatBoost, PyTorch LSTM, FinBERT, Argon2 + JWT.
- **Frontend** — Next.js 16, React 19, Tailwind, Radix UI, React
  Query, lightweight-charts, cmdk (command palette), Zod, Sonner.
