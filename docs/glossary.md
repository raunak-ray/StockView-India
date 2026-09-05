# Glossary

Stock and project terms in one line each. Grouped by topic for quick
reference. Cross-references in italics.

## Markets and exchanges

- **Stock / share** — a unit of ownership in a company.
- **NSE** — National Stock Exchange of India. The primary exchange for
  most retail trading in India.
- **BSE** — Bombay Stock Exchange. The older of the two, established
  in 1875. The "BSE" suffix in tickers (`.BO`) means BSE-listed.
- **Sensex** — BSE's flagship index of 30 large companies.
- **Nifty 50** — NSE's flagship index of 50 large companies.
- **Bank Nifty** — NSE's banking-sector index of 12 banking stocks.
- **Ticker** — the symbol used to identify a stock, e.g.
  `RELIANCE.NS` (NSE) or `RELIANCE.BO` (BSE).
- **Index** — a basket of stocks treated as a single instrument, e.g.
  Nifty 50, Bank Nifty. Not directly tradable, but index futures
  and options are.

## Price and chart terms

- **LTP** — last traded price.
- **OHLCV** — Open, High, Low, Close, Volume. The five values of a
  candle.
- **Candle** — one period (usually a day) shown as open, high, low,
  close. The body is open-to-close; the wick is the high-low range.
- **Volume** — number of shares traded in the period.
- **VWAP** — Volume-Weighted Average Price. The average price
  weighted by volume. Used as a fair-value reference.
- **Bid / Ask** — the highest price a buyer will pay (bid) and the
  lowest a seller will accept (ask). The difference is the spread.
- **Lot** — the minimum tradeable unit of a contract. For options,
  one lot is typically 25 or 50 shares.
- **Strike** — the price at which an option can be exercised.
- **Expiry** — the date on which an option contract expires.

## Indicators

- **SMA** — Simple Moving Average. The arithmetic mean of the last N
  prices. The 20-day SMA is the average of the last 20 closes.
- **EMA** — Exponential Moving Average. A weighted average that
  reacts faster to recent prices. The 20-day EMA weights the most
  recent day more than the 19 days before.
- **RSI** — Relative Strength Index. A 0–100 momentum gauge. Above
  70 = overbought; below 30 = oversold. Computed from the ratio of
  average gains to average losses over 14 days.
- **MACD** — Moving Average Convergence Divergence. The difference
  between the 12-day and 26-day EMAs. The "signal line" is the
  9-day EMA of the MACD. Crossings signal momentum shifts.
- **Bollinger Bands** — a band around the 20-day SMA, drawn at
  ±2 standard deviations. Touching the upper band = stretched up;
  touching the lower band = stretched down.
- **ATR** — Average True Range. A measure of volatility. Used for
  position sizing and stop-loss placement.
- **Donchian Channels** — the highest high and lowest low of the
  last N days. Used for breakout strategies.
- **Fibonacci retracement** — horizontal lines at 23.6%, 38.2%,
  50%, 61.8%, and 78.6% of a prior move. Used to find support and
  resistance.
- **Support / resistance** — price levels that repeatedly stopped
  falls (support) or rises (resistance). The S/R module clusters
  recent pivots to find these.
- **Stochastic** — a 0–100 oscillator that compares the close to
  the high-low range. Above 80 = overbought, below 20 = oversold.
- **ADX** — Average Directional Index. A 0–100 gauge of trend
  strength. Above 25 = strong trend, below 20 = ranging market.

## Smart Money Concepts (SMC)

- **BOS** — Break of Structure. Price breaks a prior swing high
  (uptrend) or swing low (downtrend), confirming trend continuation.
- **CHoCH** — Change of Character. Price breaks a swing in the
  opposite direction of the prevailing trend, hinting at reversal.
- **Order Block (OB)** — the last bearish candle before a strong
  rally, or the last bullish candle before a strong drop. SMC
  treats these as institutional entry zones.
- **FVG** — Fair Value Gap. A 3-candle pattern where the wicks of
  the first and third candle don't overlap, leaving a "gap" in
  price. The market tends to fill the gap later.
- **Premium / Discount** — above 50% of the range is "premium"
  (good for selling); below 50% is "discount" (good for buying).
- **Liquidity sweep** — price briefly breaks a prior high or low
  to grab stop-loss orders, then reverses.

## Verdict and signals

- **BUY / HOLD / SELL** — the app's summary opinion on a stock.
  Computed from the 3-layer fusion.
- **Confidence** — 0–100 score. Higher = the model is more sure.
  Drops when inputs (news, ML) are missing.
- **Whys** — the top 2–3 reasons the verdict was given. Plain
  English, derived from the strongest rule / feature contributions.
- **Sentiment** — mood of news headlines, scored −1 (negative) to
  +1 (positive). Computed by FinBERT (if enabled) or a 10-rule
  technical mood engine.

## Machine learning

- **Ensemble** — several models voting together instead of relying
  on one. StockView's ML uses XGBoost + LightGBM + CatBoost with
  a soft-voting layer.
- **LSTM** — Long Short-Term Memory. A recurrent neural network
  that learns from sequences of past prices. Used to predict
  tomorrow's price.
- **Walk-forward validation** — a rolling-window evaluation:
  train on days 1–N, test on day N+1, then train on days 1–N+1,
  test on day N+2, etc. Prevents future peeking.
- **SHAP** — SHapley Additive exPlanations. Attributes each
  prediction to its input features. Used to explain the ensemble
  model.
- **Feature** — an input to the ML model (e.g. RSI, MACD, volume
  ratio). The features are computed in `ml/features.py`.
- **Class imbalance** — when the target class (UP vs DOWN) is
  uneven. The model handles this with `class_weight="balanced"`
  in scikit-learn.
- **TimeSeriesSplit** — sklearn's time-series-aware K-fold. The
  test set is always ahead of the train set.

## Trading and risk

- **Stop-loss** — a pre-set exit price to limit a loss. E.g. "exit
  if RELIANCE drops below ₹2,700."
- **Target** — a pre-set price to take profit. E.g. "exit if
  RELIANCE rises above ₹2,900."
- **Trailing stop** — a stop-loss that follows the price up
  (long) or down (short). E.g. 2% trailing.
- **CAGR** — Compound Annual Growth Rate. The annualised return
  assuming profits are reinvested.
- **Sharpe ratio** — return divided by volatility. Higher = better
  risk-adjusted return.
- **Max drawdown** — the largest peak-to-trough drop in the equity
  curve. Lower = less painful ride.
- **Win rate** — fraction of trades that were profitable.
- **Profit factor** — gross profit divided by gross loss.
  Above 1.0 = profitable system.
- **Exposure** — fraction of time the strategy was in the market.
- **Slippage** — the difference between the expected fill price
  and the actual fill price. Default 0.05% in the backtest
  simulator.

## Options (NSE)

- **CE / PE** — Call European / Put European. The two option
  types. A CE is a bet that the price will rise; a PE is a bet
  it will fall.
- **PCR** — Put-Call Ratio. The volume of puts divided by the
  volume of calls. Above 1.0 = more puts than calls (bearish);
  below 0.7 = more calls (bullish).
- **Max pain** — the strike price at which the maximum number of
  options expire worthless. The price tends to drift toward
  max pain near expiry.
- **Open Interest (OI)** — the number of outstanding contracts at
  a strike. High OI = the strike is a strong support or
  resistance.
- **Implied Volatility (IV)** — the market's expectation of
  future volatility. Derived from option prices.

## Flows and breadth

- **FII** — Foreign Institutional Investors. Their net buying
  (FII net = FII buys − FII sells) is a major market driver.
- **DII** — Domestic Institutional Investors. Indian mutual
  funds, insurance companies, etc.
- **Advances / declines** — number of stocks that closed up vs
  down today. Used to gauge market breadth.
- **Sector** — a group such as banks, IT, or pharma. The sectors
  page groups stocks by GICS sector.

## Security and auth

- **Argon2** — the password hashing algorithm. Memory-hard,
  resistant to GPU attacks. Used in `auth/service.py`.
- **JWT** — JSON Web Token. The format of the access token.
  Signed with HS256, contains the user ID and expiry.
- **Access token** — short-lived (15 min), sent with every API
  request. Stored in an HttpOnly cookie.
- **Refresh token** — long-lived (7 days), used to mint new
  access tokens. Stored in HttpOnly cookie and hashed in the
  database. Rotates on every use.
- **HttpOnly cookie** — a cookie that JavaScript cannot read.
  Prevents XSS-token-stealing.
- **SameSite=Lax** — cookie attribute that prevents cross-site
  request forgery. "Lax" allows top-level navigation; "Strict"
  would block it.
- **Rate limit** — per-IP cap on requests. 10/minute on login,
  60/minute on default. Returns 429 when exceeded.

## Project terms

- **Module** — a backend unit with one router, one service, and
  optional models / schemas. 13 modules in total.
- **Page** — a frontend route. 12 pages in total.
- **Hook** — a React Query wrapper around an API call. 30+ hooks
  in `frontend/lib/hooks/`.
- **Service** — a backend function that does the work. Services
  are pure(ish) — they take inputs and return outputs, side
  effects are explicit.
- **Schema** — a Pydantic model for request/response validation.
- **Router** — a FastAPI router that maps URL paths to service
  calls.
- **Squarified treemap** — the algorithm used to lay out the
  sectors page. Each rectangle's area is proportional to a value
  (e.g. market cap), and rectangles are as square as possible.
- **FinBERT** — a financial-distilbert model for sentiment
  classification. Optional; loaded when `SV_ENABLE_FINBERT=true`.
- **TraderBuddies** — the Pine Script that the SMC module ports
  to Python. The credit is in the SMC docs.
- **Bruls et al. 2000** — the paper that introduced the
  squarified treemap algorithm.

## Related

- [Architecture](architecture.md) — the big picture.
- [Database](database.md) — the schema.
- [Setup](setup.md) — the lingo you'll see in the terminal.
- [Viva questions](viva-questions.md) — questions examiners ask.