# Instruments — Overview

**Plain words:** the searchable catalogue of Indian stocks the app knows:
about **646 NSE/BSE tickers**, each with its sector. When you press ⌘K and
type "reli", this module finds RELIANCE.

## Endpoints

| Method & path | What it does |
|---|---|
| `GET /api/v1/instruments` | Full list (~646 entries) |
| `GET /api/v1/instruments/search?q=rel` | Filtered matches |

Matches by ticker **or** company name, case-insensitive.

## Where the list comes from

Extracted once from the old prototype into
`app/modules/instruments/data/instrument_master.json`, seeded into the
database by `backend/scripts/seed_instruments.py`. The list rarely changes,
so it's treated as static.

## Where the code lives

`backend/app/modules/instruments/`. Tests: `backend/tests/test_instruments.py`.

## Good to know

- A **ticker** is a stock's short exchange code: RELIANCE, TCS, INFY.
  `.NS` = NSE, `.BO` = BSE.
- Index tickers (like `^NSEI` for NIFTY 50) are included on purpose.
