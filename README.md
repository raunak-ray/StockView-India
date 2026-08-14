# StockView India

Monorepo: FastAPI backend (`backend/`) + Next.js frontend (`frontend/`). Planning docs and the legacy Streamlit app (`app.py`) are gitignored.

## Backend (FastAPI) — Ubuntu

Requires Python 3.12+ (venv already created at `backend/.venv`). If a fresh setup is needed:

```bash
cd backend
python3 -m venv .venv          # uses system python (3.12/3.13/3.14 all work)
source .venv/bin/activate
pip install -e .
```

Optional ML-heavy extras (LSTM, FinBERT, SHAP):

```bash
pip install -e ".[ml-heavy]"
```

Dev tools:

```bash
pip install -e ".[dev]"
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Check it at http://localhost:8000 (docs at http://localhost:8000/docs).

## Frontend (Next.js) — Ubuntu

Requires Node 18.18+ (verify with `node -v`). Setup and run (run from `frontend/`):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.
