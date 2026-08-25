"""Price-alert store — verbatim port of app.py:5221–5314.

In-memory per-user state (matches Streamlit session_state pattern).
Every GET request re-checks alerts against live prices (same as Streamlit
page rerun). No background worker — identical behaviour to app.py.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.modules.market_data import service as market_data

log = logging.getLogger(__name__)


@dataclass
class Alert:
    id: str
    symbol: str
    price: float
    condition: str          # "above" | "below"
    label: str              # "📈 Crosses Above" | "📉 Crosses Below"
    created: str
    triggered: bool = False


# ── In-memory store (per-user → per-session; here one shared dict) ─────────
_store: dict[str, list[Alert]] = {}


def get_user_alerts(user_id: str) -> list[Alert]:
    return _store.get(user_id, [])


def add_alert(
    user_id: str,
    symbol: str,
    price: float,
    condition: str,
    label: str,
) -> Alert | None:
    """Add alert. Returns None if duplicate already exists."""
    alerts = _store.setdefault(user_id, [])
    existing = {(a.symbol, a.price, a.condition) for a in alerts}
    if (symbol, price, condition) in existing:
        return None
    alert = Alert(
        id=uuid.uuid4().hex[:12],
        symbol=symbol,
        price=price,
        condition=condition,
        label=label,
        created=datetime.now(tz=UTC).strftime("%H:%M:%S"),
    )
    alerts.append(alert)
    return alert


def delete_alert(user_id: str, alert_id: str) -> bool:
    alerts = _store.get(user_id, [])
    for i, a in enumerate(alerts):
        if a.id == alert_id:
            alerts.pop(i)
            return True
    return False


def clear_triggered(user_id: str) -> None:
    alerts = _store.get(user_id, [])
    _store[user_id] = [a for a in alerts if not a.triggered]


def clear_all(user_id: str) -> None:
    _store.pop(user_id, None)


async def check_alerts(user_id: str) -> list[Alert]:
    """Re-check every active alert against live price (app.py:5241-5254)."""
    alerts = _store.get(user_id, [])
    triggered_now: list[Alert] = []
    for alert in alerts:
        if alert.triggered:
            continue
        try:
            quote = await market_data.get_quote(alert.symbol)
            chk_price = quote.get("lastPrice", alert.price) if quote else alert.price
        except (KeyError, ValueError, TypeError):
            chk_price = alert.price
        hit = (
            (alert.condition == "above" and chk_price >= alert.price)
            or (alert.condition == "below" and chk_price <= alert.price)
        )
        if hit:
            alert.triggered = True
            triggered_now.append(alert)
    return triggered_now
