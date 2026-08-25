import pytest

from app.modules.alerts.service import (
    Alert,
    add_alert,
    check_alerts,
    clear_all,
    clear_triggered,
    delete_alert,
    get_user_alerts,
)


def _reset():
    from app.modules.alerts import service

    service._store.clear()


@pytest.fixture(autouse=True)
def _clean():
    _reset()
    yield
    _reset()


def test_add_and_list():
    a = add_alert("u1", "RELIANCE.NS", 2800.0, "above", "📈 Crosses Above")
    assert a is not None
    assert a.symbol == "RELIANCE.NS"
    assert a.condition == "above"
    assert a.triggered is False
    alerts = get_user_alerts("u1")
    assert len(alerts) == 1
    assert alerts[0].price == 2800.0


def test_duplicate_rejected():
    add_alert("u1", "SBIN.NS", 600.0, "below", "📉 Crosses Below")
    dup = add_alert("u1", "SBIN.NS", 600.0, "below", "📉 Crosses Below")
    assert dup is None
    assert len(get_user_alerts("u1")) == 1


def test_delete():
    a = add_alert("u1", "TCS.NS", 3500.0, "above", "📈 Crosses Above")
    assert a is not None
    assert delete_alert("u1", a.id) is True
    assert len(get_user_alerts("u1")) == 0
    assert delete_alert("u1", "nonexistent") is False


def test_clear_triggered():
    a1 = add_alert("u1", "A.NS", 100.0, "above", "📈 Crosses Above")
    a2 = add_alert("u1", "B.NS", 200.0, "above", "📈 Crosses Above")
    assert a1 is not None and a2 is not None
    a1.triggered = True
    clear_triggered("u1")
    remaining = get_user_alerts("u1")
    assert len(remaining) == 1
    assert remaining[0].id == a2.id


def test_clear_all():
    add_alert("u1", "A.NS", 100.0, "above", "📈 Crosses Above")
    add_alert("u1", "B.NS", 200.0, "below", "📉 Crosses Below")
    clear_all("u1")
    assert len(get_user_alerts("u1")) == 0


def test_user_isolation():
    add_alert("u1", "A.NS", 100.0, "above", "📈 Crosses Above")
    add_alert("u2", "B.NS", 200.0, "below", "📉 Crosses Below")
    assert len(get_user_alerts("u1")) == 1
    assert len(get_user_alerts("u2")) == 1


def test_condition_values():
    a = add_alert("u1", "INFY.NS", 1500.0, "above", "📈 Crosses Above")
    assert a is not None
    assert a.condition == "above"
    b = add_alert("u1", "INFY.NS", 1400.0, "below", "📉 Crosses Below")
    assert b is not None
    assert b.condition == "below"
    alerts = get_user_alerts("u1")
    assert len(alerts) == 2
