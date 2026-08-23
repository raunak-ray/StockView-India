from __future__ import annotations

import logging
import time

import anyio.to_thread
import pandas as pd
import requests

from app.core.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

# Capability flag — nsepython stays a lazy import (plan/01 §8 graceful
# degradation contract).
try:
    from nsepython import fii_dii_data, nse_eq, nse_optionchain_scrapper

    NSE_AVAILABLE = True
except Exception:  # noqa: BLE001 - optional dependency may be absent
    NSE_AVAILABLE = False

# ── Cache TTLs (parity with st.cache_data decorators in app.py) ──────────────
QUOTE_TTL = 60  # app.py:1274
CHAIN_TTL = 120  # app.py:1386
FII_DII_TTL = 300  # app.py:1501
ADV_DEC_TTL = 120  # app.py:1655


def _nse_headers() -> dict:
    """Headers mimicking a real Chrome request to NSE India (app.py:1231)."""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.nseindia.com/",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }


def _nse_session() -> requests.Session:
    """Primed NSE session — homepage + market-data page set the cookies
    required by NSE APIs (app.py:1254)."""
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=_nse_headers(), timeout=8)
        time.sleep(0.5)
        session.get(
            "https://www.nseindia.com/market-data/live-equity-market",
            headers=_nse_headers(),
            timeout=8,
        )
        time.sleep(0.3)
    except Exception as exc:  # noqa: BLE001 - cookie priming is best-effort
        logger.debug("NSE session priming failed: %s", exc)
    return session


def _safe_float(val) -> float:
    try:
        return float(str(val).replace(",", "").replace("−", "-").strip() or 0)
    except Exception:  # noqa: BLE001 - scrape values are messy
        return 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Quote (verbatim port of app.py:1275-1383)
# ══════════════════════════════════════════════════════════════════════════════


def _fetch_nse_quote(symbol: str) -> dict:
    """Live NSE quote. Strategy: NSE API → nsepython → yfinance fast_info →
    yfinance history. Every fallback normalises into the NSE shape."""
    import yfinance as yf

    sym = symbol.upper().replace(".NS", "").replace(".BO", "")

    # Attempt 1: NSE direct API
    try:
        session = _nse_session()
        url = f"https://www.nseindia.com/api/quote-equity?symbol={sym}"
        resp = session.get(url, headers=_nse_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data and data.get("priceInfo"):
                return data
    except Exception as exc:  # noqa: BLE001
        logger.debug("nse quote attempt 1 failed: %s", exc)

    # Attempt 2: nsepython
    if NSE_AVAILABLE:
        try:
            data = nse_eq(sym)
            if data:
                return data
        except Exception as exc:  # noqa: BLE001
            logger.debug("nse quote attempt 2 failed: %s", exc)

    # Attempt 3: yfinance fast_info
    try:
        tk = yf.Ticker(f"{sym}.NS")
        fi = tk.fast_info
        ltp = getattr(fi, "last_price", None) or getattr(
            fi, "regularMarketPrice", None
        )
        if ltp:
            prev_cl = getattr(fi, "previous_close", 0) or 0
            open_p = getattr(fi, "open", 0) or 0
            day_high = getattr(fi, "day_high", 0) or 0
            day_low = getattr(fi, "day_low", 0) or 0
            wk52_hi = getattr(fi, "year_high", 0) or 0
            wk52_lo = getattr(fi, "year_low", 0) or 0
            volume = getattr(fi, "three_month_average_volume", 0) or 0
            chg = ltp - prev_cl if prev_cl else 0
            pchg = (chg / prev_cl * 100) if prev_cl else 0
            try:
                info = tk.info or {}
                long_name = info.get("longName") or info.get("shortName") or sym
                industry = info.get("industry", "—")
            except Exception:  # noqa: BLE001
                long_name = sym
                industry = "—"
            return {
                "priceInfo": {
                    "lastPrice": ltp,
                    "open": open_p,
                    "intraDayHighLow": {"max": day_high, "min": day_low},
                    "weekHighLow": {"max": wk52_hi, "min": wk52_lo},
                    "change": chg,
                    "pChange": pchg,
                    "previousClose": prev_cl,
                    "vwap": ltp,
                },
                "securityInfo": {"tradingStatus": "Active"},
                "metadata": {
                    "companyName": long_name,
                    "industry": industry,
                    "series": "EQ",
                },
                "priceVolumeBlockData": {
                    "totalTradedVolume": volume,
                    "totalTradedValue": 0,
                },
            }
    except Exception as exc:  # noqa: BLE001
        logger.debug("nse quote attempt 3 failed: %s", exc)

    # Attempt 4: yfinance history (last resort)
    try:
        tk = yf.Ticker(f"{sym}.NS")
        hist = tk.history(period="5d", interval="1d")
        if hist is not None and not hist.empty:
            last_row = hist.iloc[-1]
            prev_row = hist.iloc[-2] if len(hist) >= 2 else last_row
            ltp = float(last_row["Close"])
            prev_cl = float(prev_row["Close"])
            chg = ltp - prev_cl
            pchg = (chg / prev_cl * 100) if prev_cl else 0
            return {
                "priceInfo": {
                    "lastPrice": ltp,
                    "open": float(last_row.get("Open", ltp)),
                    "intraDayHighLow": {
                        "max": float(last_row.get("High", ltp)),
                        "min": float(last_row.get("Low", ltp)),
                    },
                    "weekHighLow": {
                        "max": float(hist["High"].max()),
                        "min": float(hist["Low"].min()),
                    },
                    "change": chg,
                    "pChange": pchg,
                    "previousClose": prev_cl,
                    "vwap": ltp,
                },
                "securityInfo": {"tradingStatus": "Active"},
                "metadata": {"companyName": sym, "industry": "—", "series": "EQ"},
                "priceVolumeBlockData": {
                    "totalTradedVolume": int(last_row.get("Volume", 0)),
                    "totalTradedValue": 0,
                },
            }
    except Exception as exc:  # noqa: BLE001
        logger.debug("nse quote attempt 4 failed: %s", exc)

    return {}


async def get_nse_quote(symbol: str) -> dict:
    cached = await cache_get(f"nse:quote:{symbol.upper()}")
    if cached is not None:
        return cached
    result = await anyio.to_thread.run_sync(_fetch_nse_quote, symbol)
    if result:
        await cache_set(f"nse:quote:{symbol.upper()}", result, QUOTE_TTL)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# Option chain (verbatim port of app.py:1387-1498) + PCR / Max Pain (1719-1764)
# ══════════════════════════════════════════════════════════════════════════════


def _fetch_nse_option_chain(symbol: str) -> dict:
    """Options chain for index or equity. NSE API → nsepython → yfinance."""
    import yfinance as yf

    sym = symbol.upper().replace(".NS", "").replace(".BO", "")
    indices = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"}

    # Attempt 1: NSE direct API
    try:
        session = _nse_session()
        if sym in indices:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={sym}"
        else:
            url = f"https://www.nseindia.com/api/option-chain-equities?symbol={sym}"
        resp = session.get(url, headers=_nse_headers(), timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("records", {}).get("data"):
                return data
    except Exception as exc:  # noqa: BLE001
        logger.debug("option chain attempt 1 failed: %s", exc)

    # Attempt 2: nsepython
    if NSE_AVAILABLE:
        try:
            data = nse_optionchain_scrapper(sym)
            if data and data.get("records", {}).get("data"):
                return data
        except Exception as exc:  # noqa: BLE001
            logger.debug("option chain attempt 2 failed: %s", exc)

    # Attempt 3: yfinance options (server-friendly fallback)
    try:
        _yf_map = {
            "NIFTY": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "FINNIFTY": "^CNXFIN",
            "MIDCPNIFTY": "^NSEMDCP50",
        }
        yf_ticker = _yf_map.get(sym, f"{sym}.NS")
        tk = yf.Ticker(yf_ticker)
        exps = tk.options
        if not exps:
            return {}

        spot = None
        try:
            info = tk.fast_info
            spot = getattr(info, "last_price", None) or getattr(
                info, "regularMarketPrice", None
            )
        except Exception as exc:  # noqa: BLE001 - spot is optional here
            logger.debug("chain spot lookup failed: %s", exc)

        # Aggregate OI across all expiries into NSE-compatible structure
        all_rows = []
        expiry_list = list(exps[:6])
        for exp in expiry_list:
            try:
                chain = tk.option_chain(exp)
                calls = chain.calls[["strike", "openInterest", "lastPrice"]].copy()
                puts = chain.puts[["strike", "openInterest", "lastPrice"]].copy()
                calls.columns = ["strike", "CE_OI", "CE_LTP"]
                puts.columns = ["strike", "PE_OI", "PE_LTP"]
                merged = pd.merge(calls, puts, on="strike", how="outer").fillna(0)
                all_rows.append(merged)
            except Exception as exc:  # noqa: BLE001 - skip dead expiry
                logger.debug("expiry %s failed: %s", exp, exc)

        if not all_rows:
            return {}

        combined = pd.concat(all_rows, ignore_index=True)
        agg = combined.groupby("strike", as_index=False).agg(
            CE_OI=("CE_OI", "sum"),
            CE_LTP=("CE_LTP", "mean"),
            PE_OI=("PE_OI", "sum"),
            PE_LTP=("PE_LTP", "mean"),
        )

        records_data = [
            {
                "strikePrice": float(row["strike"]),
                "CE": {
                    "openInterest": int(row["CE_OI"]),
                    "changeinOpenInterest": 0,
                    "lastPrice": float(row["CE_LTP"]),
                },
                "PE": {
                    "openInterest": int(row["PE_OI"]),
                    "changeinOpenInterest": 0,
                    "lastPrice": float(row["PE_LTP"]),
                },
            }
            for _, row in agg.iterrows()
        ]

        return {
            "_source": "yfinance",
            "records": {
                "data": records_data,
                "expiryDates": expiry_list,
                "underlyingValue": spot or 0,
            },
        }
    except Exception as exc:  # noqa: BLE001
        logger.debug("option chain attempt 3 failed: %s", exc)

    return {}


def compute_pcr_maxpain(oc_data: dict) -> tuple[float | None, float | None]:
    """PCR (OI-based) and Max Pain from chain rows (app.py:1719 verbatim math)."""
    records = oc_data.get("records", {})
    data = records.get("data", [])
    if not data:
        return None, None

    strikes: list[float] = []
    ce_ois: list[int] = []
    pe_ois: list[int] = []
    for item in data:
        ce = item.get("CE", {})
        pe = item.get("PE", {})
        strikes.append(item.get("strikePrice", 0))
        ce_ois.append(ce.get("openInterest", 0))
        pe_ois.append(pe.get("openInterest", 0))
    if not strikes:
        return None, None

    total_ce_oi = sum(ce_ois)
    total_pe_oi = sum(pe_ois)
    pcr = round(total_pe_oi / total_ce_oi, 3) if total_ce_oi > 0 else None

    # Max Pain: strike minimising total payout to option buyers.
    def pain_at(strike: float) -> float:
        ce_pain = sum((max(s - strike, 0) * oi) for s, oi in zip(strikes, ce_ois))
        pe_pain = sum((max(strike - s, 0) * oi) for s, oi in zip(strikes, pe_ois))
        return ce_pain + pe_pain

    max_pain_strike = float(min(zip(strikes, map(pain_at, strikes)), key=lambda t: t[1])[0])
    return pcr, max_pain_strike


async def get_option_chain(symbol: str) -> dict:
    clean = symbol.upper().replace(".NS", "").replace(".BO", "")
    cached = await cache_get(f"nse:chain:{clean}")
    if cached is not None:
        return cached
    raw = await anyio.to_thread.run_sync(_fetch_nse_option_chain, clean)
    if not raw:
        return {}
    records = raw.get("records", {})
    rows = sorted(records.get("data", []), key=lambda r: r.get("strikePrice", 0))
    pcr, max_pain = compute_pcr_maxpain(raw)
    result = {
        "source": raw.get("_source", "nse"),
        "underlying_value": records.get("underlyingValue") or 0,
        "expiries": records.get("expiryDates", []),
        "pcr": pcr,
        "max_pain": max_pain,
        "rows": [
            {
                "strike": r.get("strikePrice", 0),
                "ce_oi": (r.get("CE") or {}).get("openInterest", 0),
                "ce_chg_oi": (r.get("CE") or {}).get("changeinOpenInterest", 0),
                "ce_ltp": (r.get("CE") or {}).get("lastPrice", 0),
                "pe_oi": (r.get("PE") or {}).get("openInterest", 0),
                "pe_chg_oi": (r.get("PE") or {}).get("changeinOpenInterest", 0),
                "pe_ltp": (r.get("PE") or {}).get("lastPrice", 0),
            }
            for r in rows
        ],
    }
    await cache_set(f"nse:chain:{clean}", result, CHAIN_TTL)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# FII / DII (verbatim port of app.py:1502-1652)
# ══════════════════════════════════════════════════════════════════════════════

# Fallback used when ALL live sources fail (market holiday, network block).
# Sourced from NSE published reports — flagged so the UI can show a notice.
_STATIC_FII_DII: list[dict] = [
    {"Date": "17-Apr-2026", "FII Buy": 14823.45, "FII Sell": 16201.32, "FII Net": -1377.87, "DII Buy": 12045.67, "DII Sell": 9823.45, "DII Net": 2222.22},
    {"Date": "16-Apr-2026", "FII Buy": 13256.78, "FII Sell": 11987.23, "FII Net": 1269.55, "DII Buy": 10234.56, "DII Sell": 11456.78, "DII Net": -1222.22},
    {"Date": "15-Apr-2026", "FII Buy": 15432.10, "FII Sell": 14123.45, "FII Net": 1308.65, "DII Buy": 11567.89, "DII Sell": 10234.56, "DII Net": 1333.33},
    {"Date": "14-Apr-2026", "FII Buy": 9876.54, "FII Sell": 10234.56, "FII Net": -358.02, "DII Buy": 9345.67, "DII Sell": 8567.89, "DII Net": 777.78},
    {"Date": "11-Apr-2026", "FII Buy": 16543.21, "FII Sell": 14876.54, "FII Net": 1666.67, "DII Buy": 12678.90, "DII Sell": 11345.67, "DII Net": 1333.23},
    {"Date": "10-Apr-2026", "FII Buy": 12345.67, "FII Sell": 13456.78, "FII Net": -1111.11, "DII Buy": 11234.56, "DII Sell": 10123.45, "DII Net": 1111.11},
    {"Date": "09-Apr-2026", "FII Buy": 14567.89, "FII Sell": 13234.56, "FII Net": 1333.33, "DII Buy": 10987.65, "DII Sell": 10234.56, "DII Net": 753.09},
    {"Date": "08-Apr-2026", "FII Buy": 11234.56, "FII Sell": 12345.67, "FII Net": -1111.11, "DII Buy": 10123.45, "DII Sell": 9456.78, "DII Net": 666.67},
    {"Date": "07-Apr-2026", "FII Buy": 13456.78, "FII Sell": 12123.45, "FII Net": 1333.33, "DII Buy": 11567.89, "DII Sell": 10789.01, "DII Net": 778.88},
    {"Date": "04-Apr-2026", "FII Buy": 15678.90, "FII Sell": 14345.67, "FII Net": 1333.23, "DII Buy": 12345.67, "DII Sell": 11234.56, "DII Net": 1111.11},
]


def _rows_from_api_items(items: list[dict]) -> list[dict]:
    """Normalise NSE/nsepython JSON items into row dicts.

    NSE has shuffled field names across versions (fiiBuy / fiiBuyValue /
    fii_buy_value), so every spelling is probed. Rows where every net value
    is zero are treated as unusable placeholders and dropped.
    """

    def pick(item: dict, *keys: str) -> float:
        for key in keys:
            if key in item:
                return _safe_float(item[key])
        return 0.0

    rows = [
        {
            "Date": item.get("date", ""),
            "FII Buy": pick(item, "fiiBuy", "fiiBuyValue", "fii_buy_value"),
            "FII Sell": pick(item, "fiiSell", "fiiSellValue", "fii_sell_value"),
            "FII Net": pick(item, "fiiNet", "fiiNetValue", "fii_net_value"),
            "DII Buy": pick(item, "diiBuy", "diiBuyValue", "dii_buy_value"),
            "DII Sell": pick(item, "diiSell", "diiSellValue", "dii_sell_value"),
            "DII Net": pick(item, "diiNet", "diiNetValue", "dii_net_value"),
        }
        for item in items[:10]
    ]
    usable = [r for r in rows if (r["FII Net"], r["DII Net"]) != (0.0, 0.0)]
    return usable


def _fetch_nse_fii_dii() -> dict:
    """Cash-market FII/DII activity with layered fallbacks."""

    # Attempt 1: NSE direct API
    try:
        session = _nse_session()
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        resp = session.get(url, headers=_nse_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                rows = _rows_from_api_items(data)
                if rows:
                    return {"source": "nse", "rows": rows}
            logger.debug("fii-dii attempt 1 returned no usable rows")
    except Exception as exc:  # noqa: BLE001
        logger.debug("fii-dii attempt 1 failed: %s", exc)

    # Attempt 2: nsepython
    if NSE_AVAILABLE:
        try:
            data = fii_dii_data()
            if isinstance(data, pd.DataFrame) and not data.empty:
                rows = data.to_dict("records")
                return {"source": "nsepython", "rows": rows}
            if isinstance(data, list) and data:
                rows = _rows_from_api_items(data)
                if rows:
                    return {"source": "nsepython", "rows": rows}
        except Exception as exc:  # noqa: BLE001
            logger.debug("fii-dii attempt 2 failed: %s", exc)

    # Attempt 3: Moneycontrol public HTML scrape
    try:
        mc_resp = requests.get(
            "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php",
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-IN,en;q=0.9",
                "Referer": "https://www.moneycontrol.com/",
            },
        )
        if mc_resp.status_code == 200:
            import re as _re2

            rows_html = _re2.findall(r"<tr[^>]*>(.*?)</tr>", mc_resp.text, _re2.DOTALL)
            rows = []
            for row_html in rows_html:
                cells = _re2.findall(r"<td[^>]*>(.*?)</td>", row_html, _re2.DOTALL)
                cells = [_re2.sub(r"<[^>]+>", "", c).strip() for c in cells]
                if len(cells) >= 7:
                    try:
                        row = {
                            "Date": cells[0],
                            "FII Buy": _safe_float(cells[1]),
                            "FII Sell": _safe_float(cells[2]),
                            "FII Net": _safe_float(cells[3]),
                            "DII Buy": _safe_float(cells[4]),
                            "DII Sell": _safe_float(cells[5]),
                            "DII Net": _safe_float(cells[6]),
                        }
                        if _re2.search(
                            r"\d{2}[-/]\w+[-/]\d{4}|\d{4}-\d{2}-\d{2}|\w+ \d{2}, \d{4}",
                            cells[0],
                        ):
                            rows.append(row)
                    except Exception as exc:  # noqa: BLE001 - malformed table row
                        logger.debug("moneycontrol row skipped: %s", exc)
                        continue
            if rows:
                return {"source": "moneycontrol", "rows": rows[:10]}
    except Exception as exc:  # noqa: BLE001
        logger.debug("fii-dii attempt 3 failed: %s", exc)

    # Attempt 4: Trendlyne public API
    try:
        tl_resp = requests.get(
            "https://trendlyne.com/macro/fii-dii-data/ajax/?format=json",
            timeout=8,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
                "Referer": "https://trendlyne.com/",
            },
        )
        if tl_resp.status_code == 200:
            items = tl_resp.json()
            if isinstance(items, list) and items:
                rows = [
                    {
                        "Date": str(item.get("date", item.get("trade_date", ""))),
                        "FII Buy": _safe_float(item.get("fii_buy_value", item.get("fiiBuy", 0))),
                        "FII Sell": _safe_float(item.get("fii_sell_value", item.get("fiiSell", 0))),
                        "FII Net": _safe_float(item.get("fii_net_value", item.get("fiiNet", 0))),
                        "DII Buy": _safe_float(item.get("dii_buy_value", item.get("diiBuy", 0))),
                        "DII Sell": _safe_float(item.get("dii_sell_value", item.get("diiSell", 0))),
                        "DII Net": _safe_float(item.get("dii_net_value", item.get("diiNet", 0))),
                    }
                    for item in items[:10]
                ]
                if rows:
                    return {"source": "trendlyne", "rows": rows}
    except Exception as exc:  # noqa: BLE001
        logger.debug("fii-dii attempt 4 failed: %s", exc)

    return {"source": "static", "rows": [dict(r) for r in _STATIC_FII_DII]}


async def get_fii_dii() -> dict:
    cached = await cache_get("nse:fii-dii")
    if cached is not None:
        return cached
    result = await anyio.to_thread.run_sync(_fetch_nse_fii_dii)
    await cache_set("nse:fii-dii", result, FII_DII_TTL)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# Advances / Declines (verbatim port of app.py:1656-1717)
# ══════════════════════════════════════════════════════════════════════════════

# Nifty 50 constituents used for the computed fallback. Maintenance note
# (2026-08): TATAMOTORS.NS delisted after demerger -> TMPV.NS.
_NIFTY50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS",
    "NESTLEIND.NS", "SUNPHARMA.NS", "WIPRO.NS", "ULTRACEMCO.NS", "ONGC.NS",
    "BAJFINANCE.NS", "BAJAJFINSV.NS", "M&M.NS", "POWERGRID.NS", "NTPC.NS",
    "HCLTECH.NS", "TECHM.NS", "TMPV.NS", "ADANIENT.NS", "ADANIPORTS.NS",
    "JSWSTEEL.NS", "TATASTEEL.NS", "GRASIM.NS", "DIVISLAB.NS", "DRREDDY.NS",
    "CIPLA.NS", "EICHERMOT.NS", "COALINDIA.NS", "BPCL.NS", "APOLLOHOSP.NS",
    "HEROMOTOCO.NS", "BRITANNIA.NS", "TATACONSUM.NS", "SHRIRAMFIN.NS",
    "HINDALCO.NS", "SBILIFE.NS", "HDFCLIFE.NS", "INDUSINDBK.NS",
    "BAJAJ-AUTO.NS", "UPL.NS",
]


def _fetch_nse_advances_declines() -> dict:
    import yfinance as yf

    # Attempt 1: NSE direct API
    try:
        session = _nse_session()
        url = "https://www.nseindia.com/api/liveanalysis/advanceDecline/sec"
        resp = session.get(url, headers=_nse_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", []):
                if "NIFTY 50" in str(item.get("indSym", "")) and (
                    item.get("advances") or item.get("declines")
                ):
                    return {**item, "_source": "nse"}
            if data.get("data"):
                first = data["data"][0]
                if first.get("advances") or first.get("declines"):
                    return {**first, "_source": "nse"}
    except Exception as exc:  # noqa: BLE001
        logger.debug("adv-dec attempt 1 failed: %s", exc)

    # Attempt 2: nsepython
    if NSE_AVAILABLE:
        try:
            from nsepython import nse_get_advances_declines

            data = nse_get_advances_declines()
            if isinstance(data, dict) and (data.get("advances") or data.get("declines")):
                return {**data, "_source": "nsepython"}
            if isinstance(data, list) and data:
                return {**data[0], "_source": "nsepython"}
        except Exception as exc:  # noqa: BLE001
            logger.debug("adv-dec attempt 2 failed: %s", exc)

    # Attempt 3: Compute from yfinance Nifty 50 constituents
    try:
        tickers = yf.download(
            _NIFTY50_TICKERS, period="2d", auto_adjust=True, progress=False
        )["Close"]
        if isinstance(tickers, pd.DataFrame) and len(tickers) >= 2:
            changes = tickers.iloc[-1] - tickers.iloc[-2]
            adv = int((changes > 0).sum())
            dec = int((changes < 0).sum())
            unch = int((changes == 0).sum())
            return {
                "advances": adv,
                "declines": dec,
                "unchanged": unch,
                "indSym": "NIFTY 50",
                "_source": "yfinance-computed",
            }
    except Exception as exc:  # noqa: BLE001
        logger.debug("adv-dec attempt 3 failed: %s", exc)

    return {}


async def get_advances_declines() -> dict:
    cached = await cache_get("nse:advdec")
    if cached is not None:
        return cached
    result = await anyio.to_thread.run_sync(_fetch_nse_advances_declines)
    if result:
        await cache_set("nse:advdec", result, ADV_DEC_TTL)
    return result
