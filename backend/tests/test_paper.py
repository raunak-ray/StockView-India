"""Paper trading unit tests — the core state machine from app.py:7749-7783."""

from __future__ import annotations

import pytest

from app.modules.portfolio.paper_service import (
    _INITIAL_CASH,
    _paper_execute_sync,
    _portfolios,
    get_orders,
    get_summary,
    place_order,
    reset_portfolio,
)

USER = "test-user-1"


def _fresh_portfolio() -> dict:
    _portfolios.pop(USER, None)
    return _portfolios.setdefault(
        USER,
        {"cash": _INITIAL_CASH, "positions": {}, "orders": [], "pnl": 0.0},
    )


# ── _paper_execute_sync (verbatim port) ─────────────────────────────────────


def test_buy_deducts_cash_and_creates_position():
    pp = _fresh_portfolio()
    ok, order = _paper_execute_sync("RELIANCE.NS", "BUY", 10, 2500.0, pp)
    assert ok is True
    assert pp["cash"] == pytest.approx(100_000 - 25_000)
    assert pp["positions"]["RELIANCE.NS"] == {"qty": 10, "avg": 2500.0}
    assert order["type"] == "BUY"
    assert order["mode"] == "PAPER"


def test_buy_insufficient_cash():
    pp = _fresh_portfolio()
    ok, msg = _paper_execute_sync("RELIANCE.NS", "BUY", 100, 2500.0, pp)
    assert ok is False
    assert "Insufficient cash" in msg


def test_sell_reduces_position_and_adds_pnl():
    pp = _fresh_portfolio()
    _paper_execute_sync("RELIANCE.NS", "BUY", 10, 2000.0, pp)
    ok, order = _paper_execute_sync("RELIANCE.NS", "SELL", 5, 2200.0, pp)
    assert ok is True
    assert pp["positions"]["RELIANCE.NS"]["qty"] == 5
    assert pp["pnl"] == pytest.approx((2200 - 2000) * 5)
    assert order["type"] == "SELL"


def test_sell_closes_position_completely():
    pp = _fresh_portfolio()
    _paper_execute_sync("TCS.NS", "BUY", 5, 3500.0, pp)
    ok, _ = _paper_execute_sync("TCS.NS", "SELL", 5, 3600.0, pp)
    assert ok is True
    assert "TCS.NS" not in pp["positions"]
    assert pp["pnl"] == pytest.approx((3600 - 3500) * 5)


def test_sell_not_enough_shares():
    pp = _fresh_portfolio()
    _paper_execute_sync("INFY.NS", "BUY", 3, 1500.0, pp)
    ok, msg = _paper_execute_sync("INFY.NS", "SELL", 10, 1500.0, pp)
    assert ok is False
    assert "Not enough shares" in msg


def test_buy_multiple_times_averages_cost():
    pp = _fresh_portfolio()
    _paper_execute_sync("SBIN.NS", "BUY", 10, 600.0, pp)
    _paper_execute_sync("SBIN.NS", "BUY", 10, 700.0, pp)
    pos = pp["positions"]["SBIN.NS"]
    assert pos["qty"] == 20
    assert pos["avg"] == pytest.approx(650.0)


# ── Service-level API ───────────────────────────────────────────────────────


def test_place_order_buy_and_get_summary():
    _fresh_portfolio()
    order = place_order(USER, "HDFCBANK.NS", "BUY", 5, 1600.0)
    assert order["symbol"] == "HDFCBANK.NS"
    assert order["qty"] == 5
    summary = get_summary(USER)
    assert summary["cash"] == pytest.approx(100_000 - 8_000)
    assert summary["positions_count"] == 1
    assert summary["orders_count"] == 1
    assert summary["pnl"] == 0.0


def test_place_order_sell_bad_qty():
    _fresh_portfolio()
    with pytest.raises(Exception) as exc_info:
        place_order(USER, "RELIANCE.NS", "BUY", 10, 2500.0)
        place_order(USER, "RELIANCE.NS", "SELL", 20, 2500.0)
    # Second place_order should raise 400 because qty > held
    assert exc_info.value.status_code == 400


def test_place_order_invalid_side():
    _fresh_portfolio()
    with pytest.raises(Exception) as exc_info:
        place_order(USER, "RELIANCE.NS", "HOLD", 10, 2500.0)
    assert exc_info.value.status_code == 400


def test_get_orders_newest_first():
    _fresh_portfolio()
    place_order(USER, "A.NS", "BUY", 1, 100.0)
    place_order(USER, "B.NS", "BUY", 2, 200.0)
    orders = get_orders(USER)
    assert orders[0]["symbol"] == "B.NS"
    assert orders[1]["symbol"] == "A.NS"


def test_reset_portfolio():
    _fresh_portfolio()
    place_order(USER, "RELIANCE.NS", "BUY", 10, 2500.0)
    summary = reset_portfolio(USER)
    assert summary["cash"] == _INITIAL_CASH
    assert summary["positions_count"] == 0
    assert summary["orders_count"] == 0
    assert summary["pnl"] == 0.0
