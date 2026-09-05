# Getting started

A 5-minute walkthrough for first-time users. If you've never used
StockView, this is the page to read first.

## Prerequisites

You need a running instance of StockView. If you don't have one
yet, follow the [Setup](setup.md) guide first — it takes about 5
minutes.

You'll end up with:

- The backend running at `http://localhost:8000`.
- The frontend running at `http://localhost:3000`.
- PostgreSQL and Redis in Docker containers.

## First login

1. Open `http://localhost:3000` in a browser.
2. Click **Sign in** in the top right.
3. Use the seeded demo account:

   - **Username**: `demo`
   - **Password**: `demo123`

4. You land on the **dashboard** at `/app`. The "Indian Indices"
   cards at the top show Nifty, Sensex, and Bank Nifty. The
   numbers load within ~1 second (the backend caches the quotes
   for 60 seconds).

If the login fails, check the [Setup troubleshooting](setup.md#troubleshooting)
section.

## A real example: RELIANCE

Once you're in, let's look at a real stock.

1. **Open the search palette.** Press **⌘K** (Mac) or
   **Ctrl+K** (Windows/Linux). A dialog appears with a search
   input.

2. **Type "reliance".** After 200ms, the results appear. The top
   hit is **Reliance Industries Limited** with ticker
   `RELIANCE.NS`. Press **↵** to open it.

   (You can also click the search button in the topbar of any
   `/app/*` page.)

3. **Read the price.** At the top of the stock terminal page, you
   see the **last traded price** (e.g. ₹2,945.30), today's
   **change** (e.g. +₹18.20), and the **percent change** (e.g.
   +0.62%). Green = up, red = down.

4. **Look at the chart.** Below the price, a candlestick chart
   shows the last year of daily prices. Each candle is one day:
   the body is the open-to-close range, the wicks are the
   high-low range. Green candles closed higher; red closed
   lower.

   The chart overlays two averages: a 20-day EMA (orange) and a
   50-day SMA (blue). When the price is above both averages, the
   short-term trend is up.

5. **Read the verdict card.** Below the chart, a coloured badge
   shows the verdict: **BUY** (green), **HOLD** (yellow), or
   **SELL** (red). The verdict is the app's summary opinion,
   computed by combining chart patterns, an ML prediction, and
   news mood.

   Below the badge, two or three **"Why"** lines explain the
   reasoning. For example: "RSI is 38, suggesting the stock is
   near oversold. The ML model predicts a 55% chance of an up
   move tomorrow. Recent news is positive."

6. **Glance at the news card.** Further down, the news card
   shows recent headlines about the stock, each with a mood
   badge (green = positive, red = negative, grey = neutral).
   The mood is computed by FinBERT (if enabled) or a 10-rule
   keyword engine.

That's the main flow: search, read price + chart, read verdict,
read news.

## Other things to try

### Paper trading

Navigate to `/app/paper-trading`. You start with **₹1,00,000 in
virtual cash**. Place a buy order:

1. Type a ticker (e.g. `RELIANCE.NS`).
2. Set the quantity (e.g. 10 shares).
3. Click "Place order".

The order is recorded, your cash drops by the order value, and a
position appears in the "Open positions" table. Nothing is real —
this is a learning tool.

### Backtest a strategy

Navigate to `/app/backtest`. Pick a stock (e.g. RELIANCE), a
strategy (e.g. SMA Cross), and a date range (e.g. last 1 year).
Click "Run backtest".

The result shows:

- An **equity curve** — your ₹1,00,000 over the period.
- **Summary metrics** — CAGR, max drawdown, Sharpe, win rate.
- A **trade log** — every buy and sell.
- A **monthly returns heatmap** — green months up, red months
  down.

### Set a price alert

Navigate to `/app/alerts`. Set a watch on RELIANCE above ₹3,000.

(⚠️ Known issue: due to the `lastPrice` vs `price` bug in the
backend's alert evaluator, every active alert fires within 30
seconds of creation. The fix is documented in
[Alerts implementation](modules/alerts/implementation.md#the-fix-in-detail).)

### Compare two stocks

Navigate to `/app/compare`. Pick two stocks (e.g. RELIANCE and
TCS). The page shows them side-by-side: price chart normalised
to base 100, snapshot cards with day change, and a comparison
table with key metrics.

### Explore the sectors

Navigate to `/app/sectors`. A treemap shows the NSE universe
grouped by sector. Each rectangle is a stock; the size is the
market cap; the colour is the day's change (green = up, red =
down). Click a sector to drill in.

## What to read next

- **[Architecture](architecture.md)** — how the parts fit
  together. The diagram is helpful.
- **[Modules](modules/)** — 13 backend modules, each with an
  overview, how-it-works, and implementation file. Start with
  [Market data](modules/market-data/overview.md) and
  [Signals](modules/signals/overview.md).
- **[Pages](pages/)** — 12 frontend pages, the same 3-file
  pattern. Start with [Stock terminal](pages/stock-terminal/overview.md).
- **[Glossary](glossary.md)** — any term you don't recognise.
- **[Demo guide](demo-guide.md)** — if you're showing the
  project to someone else.

## Common first-time issues

| Symptom | Likely cause | Fix |
|---|---|---|
| "Failed to fetch" on every page | Backend not running | Start `uvicorn` in a terminal |
| Login fails with 429 | You hit the rate limit | Wait 1 minute, try again |
| NSE pages show 502 | NSE blocks your IP | Use a VPN, or stick to Yahoo-based pages |
| Chart is empty | yfinance rate limit | Wait 10 minutes |
| ML prediction takes 30+ seconds | First call trains the model | Wait — subsequent calls are fast |
| Alerts fire immediately | The `lastPrice` bug | Known; see [Alerts](modules/alerts/implementation.md) |

For more, see the [Setup troubleshooting](setup.md#troubleshooting)
section.