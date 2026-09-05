# Alerts — what it is

The Alerts page is the **price alert manager at `/app/alerts`**. It lets
you set alerts on any NSE stock — "tell me when RELIANCE crosses above
₹2,800" or "tell me when INFY drops below ₹1,400". The backend polls
live prices and marks alerts as fired when the condition is met.

It is the "wake me up when..." page. Useful for traders who watch
specific levels and want to know the moment a price breaks through.

## What visitors see

A title "Price Alerts" and a single create-alert card. Below the form,
two sections:

| Section | What it is |
|---|---|
| **Watching** | Active alerts (condition not yet met). Cleared by the "Clear all" button. |
| **Triggered** | Fired alerts (condition was met). Cleared by the "Clear triggered" button. |

The create form has three fields:

1. **Symbol** — A `SymbolSearch` input.
2. **Price (₹)** — A number input.
3. **Condition** — A dropdown: "Crosses Above" or "Crosses Below".

Submit with the "+ Add Alert" button (gold-coloured).

## A real example

You set three alerts on a Monday morning:

1. RELIANCE.NS above ₹2,800.
2. INFY.NS below ₹1,400.
3. HDFCBANK.NS above ₹1,700.

The page shows three active rows:

- **Watching (3)**:
  - RELIANCE.NS · ABOVE · ₹2,800 · Set Mon 10:30
  - INFY.NS · BELOW · ₹1,400 · Set Mon 10:31
  - HDFCBANK.NS · ABOVE · ₹1,700 · Set Mon 10:32

By Wednesday, RELIANCE has crossed ₹2,800. The backend marks the alert
as fired. The page now shows:

- **Watching (2)**: INFY, HDFCBANK.
- **Triggered (1)**: RELIANCE — with a red border, a struck-out
  bell icon (BellOff), and the "X" delete button.

You click "Clear triggered" to remove the fired alert. The page is
back to two watching.

## The two alert states

| State | What it means | Visual |
|---|---|---|
| **Active / Watching** | The condition has not been met. The alert is live. | Gold bell, gold border, normal row |
| **Fired / Triggered** | The condition was met. The alert is in the history. | Red BellOff, red border, red-tinted background |

When an alert is created, it starts as "active". When the backend's
polling logic detects the condition was met (e.g. last price crossed
above the threshold), the alert is moved to "fired" and remains there
until the user deletes it or clears the fired list.

## What the page does not do

- **It does not push notifications.** Fired alerts only show on the
  page (and in the user's session). No email, no SMS, no push.
- **It does not support "touches" vs "crosses" semantics.** A simple
  above/below threshold. The backend may interpret "crosses" as
  "last price at or above" — see the [implementation file](implementation.md)
  for the exact check.
- **It does not support percentage-based alerts.** Only absolute price
  thresholds.
- **It does not persist across server restarts.** The alert store is
  in-memory. A server restart wipes all alerts.
- **It does not show a notification toast** when an alert fires. The
  user has to navigate to the page to see fired alerts.

## Where it lives in the codebase

- Page: `frontend/app/(app)/app/alerts/page.tsx` (244 lines)
- API client: `frontend/lib/api/alerts.ts`
- Hook: `frontend/lib/hooks/use-alerts.ts`
- Backend: [alerts module](../../modules/alerts/overview.md)
- Components used:
  - `SymbolSearch` from `@/components/symbol-search`
  - `Select` from `@/components/ui/select`

## Backend modules used

- [Alerts](../../modules/alerts/overview.md) — the primary backend. The page calls
  `GET /alerts`, `POST /alerts`, `DELETE /alerts/{id}`, and `DELETE /alerts` (clear).
- [Market data](../../modules/market-data/overview.md) — the alert evaluator uses
  `GET /quote` to check the threshold every 30s. **The `lastPrice` bug is in this
  call site** — see the [implementation file](implementation.md) for the fix.
- [Instruments](../../modules/instruments/overview.md) — symbol search in the create form.

## Related pages in this folder

- [How it works](how-it-works.md) — the form state, the create flow,
  the two alert lists, the clear flows, the known bug in the
  backend's market-data lookup.
- [Implementation](implementation.md) — file map, the bug
  documentation, every hook, the request traces.

## A note on a known bug

The backend's alert evaluation uses `quote.get("lastPrice", ...)` to
look up the live price. The market-data response uses the key `price`,
not `lastPrice`. This means the lookup always falls back to the
alert's stored price, and every active alert fires immediately on the
next list call.

The bug is documented in the [alerts module docs](../../modules/alerts/implementation.md)
and the [alerts page implementation](implementation.md). The fix is a
4-line change in `backend/app/modules/alerts/service.py`.