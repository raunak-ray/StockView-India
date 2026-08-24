"""Paper trading service — in-memory portfolio state machine.

Port of app.py:7749-7783 (_paper_execute) and the session_state
paper_portfolio dict (cash ₹1,00,000, positions, orders, P&L).

State is per-user and lives in process memory — resets on server restart,
same as the original Streamlit session_state approach. Broker connectors
(Kite, Upstox, Binance, Angel One) are flagged as future work.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from app.modules.market_data import service as market_data

# ── Per-user portfolio state (in-memory, parity with Streamlit session) ────

_INITIAL_CASH = 100_000.0  # ₹1,00,000

_portfolios: dict[str, dict[str, Any]] = {}


def _get_portfolio(user_id: str) -> dict[str, Any]:
    if user_id not in _portfolios:
        _portfolios[user_id] = {
            "cash": _INITIAL_CASH,
            "positions": {},   # {symbol: {"qty": int, "avg": float}}
            "orders": [],      # list of order dicts
            "pnl": 0.0,        # realised P&L
        }
    return _portfolios[user_id]


# ── Paper execute (verbatim port of app.py:7749-7783) ───────────────────────


def _paper_execute_sync(
    symbol: str, txn_type: str, qty: int, price: float, portfolio: dict
) -> tuple[bool, str | dict]:
    """Simulate order execution — same logic as app.py _paper_execute."""
    cost = round(qty * price, 2)

    if txn_type == "BUY":
        if portfolio["cash"] < cost:
            return False, f"Insufficient cash (need ₹{cost:,.0f}, have ₹{portfolio['cash']:,.0f})"
        portfolio["cash"] -= cost
        pos = portfolio["positions"].get(symbol, {"qty": 0, "avg": 0.0})
        new_qty = pos["qty"] + qty
        new_avg = round((pos["qty"] * pos["avg"] + cost) / new_qty, 2)
        portfolio["positions"][symbol] = {"qty": new_qty, "avg": new_avg}
    else:  # SELL
        pos = portfolio["positions"].get(symbol, {"qty": 0, "avg": 0.0})
        if pos["qty"] < qty:
            return False, f"Not enough shares (have {pos['qty']}, want to sell {qty})"
        proceeds = round(qty * price, 2)
        pnl = round((price - pos["avg"]) * qty, 2)
        portfolio["cash"] += proceeds
        portfolio["pnl"] += pnl
        new_qty = pos["qty"] - qty
        if new_qty == 0:
            portfolio["positions"].pop(symbol, None)
        else:
            portfolio["positions"][symbol]["qty"] = new_qty

    order = {
        "id": str(uuid.uuid4())[:8].upper(),
        "ts": datetime.now(UTC).isoformat(),
        "symbol": symbol,
        "type": txn_type,
        "qty": qty,
        "price": price,
        "value": cost,
        "mode": "PAPER",
    }
    portfolio["orders"].append(order)
    return True, order


# ── Public API ──────────────────────────────────────────────────────────────


def get_summary(user_id: str) -> dict[str, Any]:
    """Portfolio summary: cash, position count, order count, realised P&L."""
    pp = _get_portfolio(user_id)
    return {
        "cash": round(pp["cash"], 2),
        "positions_count": len(pp["positions"]),
        "orders_count": len(pp["orders"]),
        "pnl": round(pp["pnl"], 2),
        "initial_cash": _INITIAL_CASH,
    }


def place_order(user_id: str, symbol: str, side: str, qty: int, price: float) -> dict:
    """Place a paper order. Returns the executed order dict."""
    if qty <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Quantity must be positive.")
    if price <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Price must be positive.")
    if side not in ("BUY", "SELL"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Side must be BUY or SELL.")

    portfolio = _get_portfolio(user_id)
    ok, result = _paper_execute_sync(symbol.strip().upper(), side, qty, price, portfolio)

    if not ok:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(result))
    assert isinstance(result, dict)
    return result


async def get_positions(user_id: str) -> list[dict]:
    """List open positions with live P&L enrichment."""
    pp = _get_portfolio(user_id)
    positions = []
    for sym, pos in pp["positions"].items():
        ltp = pos["avg"]  # fallback to avg cost
        try:
            quote = await market_data.get_quote(sym)
            ltp = float(quote.get("price", pos["avg"]))
        except Exception:  # noqa: BLE001, S110 — live price is best-effort
            pass
        unrealised = round((ltp - pos["avg"]) * pos["qty"], 2)
        pnl_pct = round((ltp - pos["avg"]) / pos["avg"] * 100, 2) if pos["avg"] else 0.0
        positions.append({
            "symbol": sym,
            "qty": pos["qty"],
            "avg_cost": round(pos["avg"], 2),
            "ltp": round(ltp, 2),
            "unrealised_pnl": unrealised,
            "pnl_pct": pnl_pct,
        })
    return positions


def get_orders(user_id: str) -> list[dict]:
    """Return order history (newest first)."""
    pp = _get_portfolio(user_id)
    return list(reversed(pp["orders"]))


def reset_portfolio(user_id: str) -> dict:
    """Reset portfolio to initial ₹1,00,000."""
    _portfolios[user_id] = {
        "cash": _INITIAL_CASH,
        "positions": {},
        "orders": [],
        "pnl": 0.0,
    }
    return get_summary(user_id)
