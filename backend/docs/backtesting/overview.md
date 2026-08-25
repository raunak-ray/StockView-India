# Backtesting — Overview

**Plain words:** replay history. "If I had followed strategy X since 2020,
how much money would I have made?" Shows the money curve, win rate, and
every trade taken.

## The no-look-ahead rule

Signal on bar[i] → trade fills at bar[i+1] Open. The engine never peeks
at tomorrow's data when deciding today's trade. This is tested by a
contract test that verifies entry prices.

## 6 strategies

| Strategy | Entry | Exit |
|---|---|---|
| SMA Crossover | SMA20 > SMA50 | SMA20 < SMA50 |
| RSI Mean Reversion | RSI < 35 | RSI > 65 |
| MACD Crossover | MACD crosses above Signal | MACD crosses below |
| Bollinger Band Bounce | Price < lower band | Price > upper band |
| EMA Trend | EMA20 > SMA50 | EMA20 < SMA50 |
| Golden Cross | SMA50 > SMA200 | SMA50 < SMA200 |

## Metrics

CAGR, Sharpe, Sortino, Calmar, max drawdown, win rate, profit factor,
expectancy, alpha vs buy-and-hold. Equity curve and monthly heatmap.

## Endpoint

`POST /api/v1/backtesting/run` with config body.
`GET /api/v1/backtesting/strategies` lists available strategies.

## Where the code lives

`backend/app/modules/backtesting/`. Tests: `tests/test_backtesting.py`.
