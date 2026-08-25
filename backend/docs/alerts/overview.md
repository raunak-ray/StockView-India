# Price Alerts — Overview

**Plain words:** "Tell me when a stock crosses a price." Set an alert, and
the next time you visit the alerts page (or the topbar bell), it checks
live prices and shows a triggered badge if the condition is met.

## How it works

Same as Streamlit's session_state — alerts live in memory per user. Every
`GET /api/v1/alerts` request re-checks all active alerts against live
market prices (via `market_data.get_quote`). No background worker needed;
behaviour is identical to the original app.py.

## Two conditions

- **Crosses Above** — alert fires when current price ≥ alert price
- **Crosses Below** — alert fires when current price ≤ alert price

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/alerts` | List active + fired alerts; also re-checks prices |
| `POST` | `/alerts` | Create alert (symbol, price, condition, label) |
| `DELETE` | `/alerts/{id}` | Delete a single alert |
| `DELETE` | `/alerts?fired_only=true` | Clear all triggered alerts |
| `DELETE` | `/alerts` | Clear all alerts |

## Where the code lives

`backend/app/modules/alerts/`. Tests: `tests/test_alerts.py`.
Frontend: `frontend/app/(app)/app/alerts/page.tsx`.
