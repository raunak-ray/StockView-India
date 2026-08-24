# Signals — Overview

**Plain words:** the app's opinion-giver. Two modes: a rule-based verdict
(signals) and a fused verdict that blends rules, ML, and news.

## Rule-based signal

- **Verdict** — BUY / WEAK BUY / HOLD / WEAK SELL / SELL
- **Score** integer (strong sell → strong buy)
- **Confidence** — 0.5–1.0, how strongly rules agree
- **Rules breakdown** — every rule's own vote (shown as chips on the site)
- **Markers** — buy/sell arrows on the chart

Endpoint: `GET /api/v1/signals?symbol=&interval=&period=`

## Fusion signal (3-layer blend)

Blends three independent opinions into **one** final verdict:

| Layer | Weight | What it is |
|---|---|---|
| Technical rules | 45% | 10 indicator checks → score −1…+1 |
| ML ensemble | 40% | XGB+LGBM+CAT up-prob → score −1…+1 |
| News NLP | 15% | FinBERT + keyword headline score −1…+1 |

If ML or news is unavailable, remaining layers re-weight proportionally.
Confidence tier: HIGH (all agree), MEDIUM (some disagree), LOW (missing layers).

Endpoint: `GET /api/v1/signals/fusion?symbol=&interval=&period=`

## Where the code lives

`backend/app/modules/signals/`. Tests: `backend/tests/test_analytics_signals.py`.
