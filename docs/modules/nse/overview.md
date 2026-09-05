# NSE — what it is

The NSE module fetches **NSE India specific data** that the Yahoo-based
`market_data` module does not cover: live option chains, FII/DII institutional
flows, and advances/declines market breadth.

This is the only module that scrapes NSE directly. Every endpoint tries
multiple data sources in priority order, and degrades gracefully when the
primary source is unreachable.

## What you can do with it

- **Get an NSE quote** for any symbol with `GET /nse/quote/{symbol}`. Returns
  the full NSE quote payload — last price, day high/low, 52-week range, volume,
  VWAP, trading status, sector.
- **Get the full option chain** for NIFTY, BANKNIFTY, or any equity with
  `GET /nse/option-chain/{symbol}`. Includes PCR and max-pain calculations.
- **Get the last 10 days of FII/DII activity** with `GET /nse/fii-dii`.
- **Get market breadth** (advances vs declines) for NIFTY 50 with
  `GET /nse/advances-declines`.

## The four endpoints at a glance

| Endpoint | Cache TTL | Data source priority | Fallback |
|---|---|---|---|
| `/nse/quote/{symbol}` | 60s | NSE API → nsepython → yfinance fast_info → yfinance history | 502 |
| `/nse/option-chain/{symbol}` | 120s | NSE API → nsepython → yfinance options | 502 |
| `/nse/fii-dii` | 300s | NSE API → nsepython → Moneycontrol HTML → Trendlyne API → static fixture | static data |
| `/nse/advances-declines` | 120s | NSE API → nsepython → computed from Nifty 50 | 502 |

All four are protected (`get_current_user`). All four are async and use
Redis caching with the listed TTLs.

## Why this module is so fallback-heavy

NSE India is **notoriously hard to scrape**:

- Cookie-based session — the homepage + market-data page must be visited
  first to set cookies before any API call.
- Heavy bot detection — bare `requests` is rejected.
- Rate limiting — repeated calls get throttled.
- Frequent shape changes — field names have been renamed multiple times.
- Geofenced — many APIs return 401/403 from non-India IPs.

So every endpoint has 3–4 fallback paths. If NSE is down, we fall back to
nsepython (a community library that handles the cookie stuff). If that
fails, we fall back to yfinance. The FII/DII endpoint has a final static
fallback so the page is never empty.

## The NSE session primer

NSE's API requires cookies set during a real browser visit. The service
handles this with a one-shot primer:

```python
def _nse_session() -> requests.Session:
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=_nse_headers(), timeout=8)
        time.sleep(0.5)
        session.get("https://www.nseindia.com/market-data/live-equity-market",
                    headers=_nse_headers(), timeout=8)
    except Exception:
        pass
    return session
```

The `_nse_headers()` helper sends a realistic Chrome user agent plus
`sec-ch-ua` and `sec-fetch-*` headers. Without these, NSE returns 401.

> On non-India IPs, even the primer often fails. The fallback chain handles
> that. Live data is best-effort; cached and computed fallbacks keep the
> page functional.

## A real example

You open NIFTY's option chain. `/nse/option-chain/NIFTY` returns:

```json
{
  "symbol": "NIFTY",
  "source": "nse",
  "underlying_value": 22850.45,
  "expiries": ["2026-04-25", "2026-05-02", "2026-05-09", "..."],
  "pcr": 1.18,
  "max_pain": 22800,
  "rows": [
    {
      "strike": 22700,
      "ce_oi": 124500, "ce_chg_oi": 12000, "ce_ltp": 165.5,
      "pe_oi": 85000, "pe_chg_oi": -5000, "pe_ltp": 15.2
    },
    ...
  ]
}
```

The frontend renders the strike ladder, the PCR gauge (1.18 = put-heavy
crowd = bullish contrarian), and the max-pain line (where option writers
profit most, often acts as a magnet for expiry).

## The two derived metrics

**PCR (Put-Call Ratio)** = `total put OI / total call OI`. Convention:

- PCR > 1.0 → more puts sold than calls → often seen as bullish
  (hedgers are protecting against drops).
- PCR < 1.0 → more calls traded → bullish speculation.
- PCR extremes (>1.5 or <0.5) → often contrarian signals.

**Max Pain** = the strike where the total payout to option buyers is
**minimised**. At expiry, price tends to gravitate toward max pain because
option writers (typically institutions) hedge in that direction.

## FII/DII activity

**FII** = Foreign Institutional Investors. **DII** = Domestic Institutional
Investors. Daily net buy/sell values in ₹ crores.

The data is institutional positioning. Persistent FII selling often
correlates with market weakness; persistent DII buying often absorbs that
selling and stabilises the market.

The response shape:

```json
{
  "source": "nse",
  "rows": [
    {
      "date": "2026-04-17",
      "fii_buy": 14823.45, "fii_sell": 16201.32, "fii_net": -1377.87,
      "dii_buy": 12045.67, "dii_sell": 9823.45, "dii_net": 2222.22
    },
    ...
  ]
}
```

## Advances / Declines

Simple counts of how many NIFTY 50 stocks ended up vs down vs flat for the
current session. Sentiment proxy:

- More advances than declines → broad market is up.
- More declines than advances → broad market is down.
- 30+/15- or worse → strong directional day.

## Where it lives in the codebase

- Backend code: `backend/app/modules/nse/`
- Backend dev notes: `backend/docs/nse/`
- Optional extra: `nsepython` (community NSE library)
- Cache: Redis via `core/cache.py`
- Frontend API client: `frontend/lib/api/nse.ts`
- Frontend hook: `frontend/lib/hooks/use-nse.ts`

## Consumed by (frontend pages)

- [Markets](../../pages/markets/overview.md) — the only consumer. The 4 tabs
  (NSE quote, FII/DII, advances/declines, options) all hit this module.
- [Dashboard](../../pages/dashboard/overview.md) — the index cards (Nifty, Sensex,
  Bank Nifty) call `get_quote` for the live price. If NSE is down, the cards fall
  through to the Yahoo Finance quote.

## Known issues

- **NSE blocks non-India IPs** — the API returns 502 / 403 outside India. The
  multi-layer fallback (Trendlyne, static fixture) keeps the page functional but
  the data may be stale.

## Related pages in this folder

- [How it works](how-it-works.md) — the fallback chain per endpoint, the
  session primer, the PCR and max-pain math, the breadth computation.
- [Implementation](implementation.md) — file map, the exact NSE URLs, the
  static fallback fixture, request traces, gotchas.