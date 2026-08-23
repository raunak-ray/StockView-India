# Signals — Overview

**Plain words:** the app's opinion-giver. It reads the indicators and applies
fixed, readable rules (the same ones a human chart trader would check) to
answer: **Buy, Hold, or Sell — and why.** Never a black box.

## What it returns

- **Verdict** — BUY / HOLD / SELL
- **Score** −15…+15 (strong sell → strong buy)
- **Confidence** — how strongly the rules agree
- **Rules breakdown** — every rule's own vote (shown as chips on the site)
- **Stop-loss** — exit price if the trade goes wrong

## Endpoint

`GET /api/v1/signals?symbol=&interval=&period=`

## Where the code lives

`backend/app/modules/signals/`. Tests: `backend/tests/test_analytics_signals.py`.

## Good to know

This is the **rule-based** signal. A later "fusion" endpoint will blend it
with the ML prediction (40%) and news mood (15%) — weights 45/40/15.
Education tool, not advice: rules describe the chart; they can't know news.
