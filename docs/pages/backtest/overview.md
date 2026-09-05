# Backtest — what it is

The Backtest page is the **strategy simulator at `/app/backtest`**. It
lets you run a historical simulation of a trading strategy on any NSE
stock and see the resulting equity curve, key metrics, and trade log.

It is the page for "would this strategy have worked?" questions. You
pick a stock, a strategy, a period, a starting capital, and risk
parameters (stop-loss, take-profit, commission). The backend runs the
strategy on up to 10 years of daily bars and returns the full result.

## What visitors see

A title "Backtesting" and a single configuration card. Below the form, a
run button. After clicking "Run Backtest" (or as soon as the previous
result is in cache), a results section appears.

The configuration card has two rows:

| Row | Fields |
|---|---|
| **Row 1** | Symbol, Strategy, Period (years) |
| **Row 2** | Capital (₹), Stop-loss %, Take-profit %, Commission % |

The result section, when present, has:

| Section | What it shows |
|---|---|
| **Header line** | Strategy · Symbol · Years, plus capital → final equity |
| **Key metrics (4 cards)** | CAGR, Sharpe, Max Drawdown, Total Return |
| **Equity curve** | A line chart of the simulated equity over time |
| **Secondary metrics (6 cards)** | Sortino, Calmar, Profit Factor, Alpha, Win Rate, Avg Hold |
| **Tabs** | Trade Log (full list), Monthly Returns (heatmap) |

## A real example

You want to test the SMA Crossover strategy on RELIANCE.NS over 5
years, with ₹1,00,000 capital, 5% stop-loss, no take-profit, and 0.1%
commission per leg.

You fill the form. Click "Run Backtest". The result appears in 1–3
seconds:

- **Header**: `SMA Crossover · RELIANCE.NS · 5y` and
  `₹1,00,000 → ₹1,42,500`.
- **Key metrics**:
  - CAGR: +8.42% (green).
  - Sharpe: 1.12 (green, "Good").
  - Max Drawdown: −12.5% (red, "63 days").
  - Total Return: +42.5% (green, "Win rate 54.2%").
- **Equity curve**: A line chart from 1.0 to 1.425 over 5 years. Some
  drawdowns, mostly upward.
- **Secondary metrics**:
  - Sortino: 1.45 (green).
  - Calmar: 0.68 (gold).
  - Profit Factor: 1.62 (green).
  - Alpha: +2.10% (green, vs buy-and-hold).
  - Win Rate: 54.2% (green, "12W · 10L").
  - Avg Hold: 18d (with expectancy ₹420).
- **Trade Log tab**: 22 trades, one per row. Each shows the entry/exit
  date, entry/exit price, P&L, and exit reason (signal, stop-loss, etc.).
- **Monthly Returns tab**: A 12-column heatmap, one cell per month. Cells
  are coloured by return % (green for positive, red for negative). A
  tooltip on hover shows the exact %.

## The strategies

The strategy dropdown is populated from the backend's
`/api/v1/backtesting/strategies` endpoint. There are 6 strategies:

| Strategy | Description |
|---|---|
| **SMA Crossover** | Buy when fast SMA crosses above slow SMA, sell on opposite cross |
| **EMA Crossover** | Same logic but with EMAs (more weight on recent prices) |
| **RSI Mean Reversion** | Buy when RSI is oversold, sell when overbought |
| **MACD Signal** | Buy on MACD line crossing above signal line, sell on opposite |
| **Bollinger Bands** | Buy at lower band, sell at middle band (mean reversion) |
| **Donchian Breakout** | Buy at N-day high, sell at N-day low (trend-following) |

The list is rendered from `strategies.data?.strategies` and is
re-fetched on each page load (no caching beyond React Query's default).

## The risk parameters

| Parameter | Default | Range | Effect |
|---|---|---|---|
| **Stop-loss %** | 5 | 0–20 | Closes the trade at a loss of X% from entry. 0 = no stop-loss. |
| **Take-profit %** | 0 | 0–50 | Closes the trade at a gain of X% from entry. 0 = exit on signal only. |
| **Commission %** | 0.1 | 0–1 | Per-leg commission in %. 0.1% on both entry and exit = 0.2% round-trip. |

The position size is fixed at 100% of capital (one position at a time).

## The metrics

| Metric | What it means |
|---|---|
| **CAGR** | Compound annual growth rate. (Final / Initial)^(1/years) − 1. |
| **Sharpe** | Risk-adjusted return. (mean_daily_return − risk_free) / std_daily_return × √252. |
| **Max Drawdown** | The largest peak-to-trough decline. Negative %. |
| **Total Return** | Final equity / initial capital − 1, in %. |
| **Sortino** | Like Sharpe but only counts downside volatility. |
| **Calmar** | CAGR / abs(Max Drawdown). Higher = better risk-adjusted. |
| **Profit Factor** | Sum of wins / abs(sum of losses). > 1.5 is good. |
| **Alpha** | Strategy CAGR − buy-and-hold CAGR. |
| **Win Rate** | Wins / total trades, in %. |
| **Avg Hold** | Average days in a trade. |

The metrics are computed by the backend's `backtesting.service`. The
frontend just displays them.

## What the page does not do

- It does not save results. Run a backtest, look at the result, run
  another. The previous result is overwritten.
- It does not support multi-symbol backtests. One symbol at a time.
- It does not support position sizing. Always 100% of capital.
- It does not support shorting. The strategies are long-only.
- It does not compare strategies side-by-side. Run them one at a time.

## Where it lives in the codebase

- Page: `frontend/app/(app)/app/backtest/page.tsx` (443 lines, all
  components inline)
- API client: `frontend/lib/api/backtest.ts`
- Hook: `frontend/lib/hooks/use-backtest.ts`
- Backend: [backtesting module](../../modules/backtesting/overview.md)
- Components used:
  - `SymbolSearch` from `@/components/symbol-search`
  - `Tabs` from `@/components/ui/tabs`

## Backend modules used

- [Backtesting](../../modules/backtesting/overview.md) — `POST /backtest` takes a symbol,
  strategy, and date range, and returns the equity curve, trade log, and metrics.
- [Market data](../../modules/market-data/overview.md) — historical OHLCV (the backtesting
  module calls this internally).
- [Analytics](../../modules/analytics/overview.md) — indicators the strategies need
  (called internally by backtesting).
- [Instruments](../../modules/instruments/overview.md) — symbol search in the form.

## Related pages in this folder

- [How it works](how-it-works.md) — the form state, the run flow, the
  result structure, the equity curve, the heatmap, the trade log.
- [Implementation](implementation.md) — file map, every metric's tone
  threshold, the heatmap colour formula, the request traces.