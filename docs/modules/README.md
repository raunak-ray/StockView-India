# Backend modules

One folder per module. Each folder has three files: a short **overview**
(what it is), a **how-it-works** walkthrough (data flow, formulas, edge
cases), and an **implementation** file (file map, every function,
request traces).

| Module | What it does | Docs |
|---|---|---|
| **Auth** | Registration, login, JWT access + rotating refresh tokens, rate limiting | [overview](auth/overview.md) · [how it works](auth/how-it-works.md) · [implementation](auth/implementation.md) · 459 lines |
| **Market data** | Prices and company info from Yahoo Finance, 5-tier Redis cache, MultiIndex handling | [overview](market-data/overview.md) · [how it works](market-data/how-it-works.md) · [implementation](market-data/implementation.md) · 484 lines |
| **Instruments** | Searchable stock catalogue, 646 NSE/BSE instruments + indices, `@lru_cache` JSON master | [overview](instruments/overview.md) · [how it works](instruments/how-it-works.md) · [implementation](instruments/implementation.md) · 399 lines |
| **Analytics** | 11 indicators (SMA, EMA, RSI, MACD, BB, ATR), support/resistance clustering, Fibonacci | [overview](analytics/overview.md) · [how it works](analytics/how-it-works.md) · [implementation](analytics/implementation.md) · 504 lines |
| **Signals** | 10-rule engine, 3-layer fusion (technical 45% + ML 40% + news 15%) with re-weighting | [overview](signals/overview.md) · [how it works](signals/how-it-works.md) · [implementation](signals/implementation.md) · 679 lines |
| **SMC** | TraderBuddies port — BOS, CHoCH, Order Blocks, Fair Value Gaps, premium/discount zones | [overview](smc/overview.md) · [how it works](smc/how-it-works.md) · [implementation](smc/implementation.md) · 570 lines |
| **Sentiment** | RSS feeds (3 sources) + FinBERT optional, 10-rule technical mood, score from −1 to +1 | [overview](sentiment/overview.md) · [how it works](sentiment/how-it-works.md) · [implementation](sentiment/implementation.md) · 725 lines |
| **ML** | Ensemble of XGBoost / LightGBM / CatBoost with scikit-learn fallback, optional PyTorch LSTM, SHAP, walk-forward validation | [overview](ml/overview.md) · [how it works](ml/how-it-works.md) · [implementation](ml/implementation.md) · 1,065 lines |
| **Backtesting** | 6 strategies (SMA/EMA cross, RSI, MACD, BB, Donchian), 20+ metrics, event-driven simulator with slippage | [overview](backtesting/overview.md) · [how it works](backtesting/how-it-works.md) · [implementation](backtesting/implementation.md) · 724 lines |
| **Alerts** | Per-user price alarms, in-memory store, background polling | [overview](alerts/overview.md) · [how it works](alerts/how-it-works.md) · [implementation](alerts/implementation.md) · 534 lines · **known bug** |
| **Portfolio** | Watchlist (PostgreSQL) + paper trading (in-memory), weighted-avg cost, 5 endpoints | [overview](portfolio/overview.md) · [how it works](portfolio/how-it-works.md) · [implementation](portfolio/implementation.md) · 675 lines |
| **NSE** | Quote, option chain (PCR + max-pain), FII/DII, advances/declines — each with multi-layer fallback | [overview](nse/overview.md) · [how it works](nse/how-it-works.md) · [implementation](nse/implementation.md) · 720 lines |
| **Compare** | 2–4 symbol side-by-side, price normalisation to base 100, in-place indicator compute | [overview](compare/overview.md) · [how it works](compare/how-it-works.md) · [implementation](compare/implementation.md) · 602 lines |

**Total: 13 modules · 39 files · 8,140 lines.**

Database storage is covered in [Database](../database.md). Setup and
troubleshooting are in [Setup](../setup.md). The architecture diagram is
in [Architecture](../architecture.md). For deep technical notes per
module (architecture decisions, formulas, edge cases beyond what is in
the docs folders), see `backend/docs/<module-name>/`.

## How to read a module

If you want a **5-minute overview** — read `overview.md` only.

If you want to **understand the algorithm** — read `how-it-works.md`. It
has the data flow, the math, the edge cases, and diagrams.

If you want to **modify the code** — read `implementation.md`. It has
the file map, every function, request traces, and gotchas. Pair with
the actual source files in `backend/app/modules/<name>/`.

For deeper notes (architecture decisions, formula derivations, known
limitations), check `backend/docs/<name>/` — the per-module dev notes
that live alongside the source code.