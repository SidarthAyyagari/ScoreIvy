import hashlib
import hmac
import importlib
import json
import time

import pytest
import stripe

from app import config
from app.models.models import Order, UserPackage
from tests.conftest import auth_headers

WEBHOOK_SECRET = "whsec_test_secret"


@pytest.fixture()
def stripe_on(monkeypatch):
    monkeypatch.setattr(config, "STRIPE_SECRET_KEY", "sk_test_dummy")
    monkeypatch.setattr(config, "STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    created = []

    def fake_create(**kwargs):
        session_id = f"cs_test_{len(created) + 1}"
        created.append(kwargs)
        return {"id": session_id, "url": f"https://checkout.stripe.com/c/pay/{session_id}"}

    monkeypatch.setattr(stripe.checkout.Session, "create", fake_create)
    return created


def _signed(payload: dict, secret: str = WEBHOOK_SECRET):
    body = json.dumps(payload)
    timestamp = int(time.time())
    signature = hmac.new(secret.encode(), f"{timestamp}.{body}".encode(), hashlib.sha256).hexdigest()
    return body, {"Stripe-Signature": f"t={timestamp},v1={signature}", "Content-Type": "application/json"}


def _event(kind: str, obj: dict) -> dict:
    return {"id": "evt_test", "object": "event", "type": kind, "data": {"object": obj}}


def _paid_session(session_id="cs_test_1", amount=4900, **overrides):
    session = {
        "id": session_id, "object": "checkout.session", "payment_status": "paid",
        "amount_total": amount, "currency": "usd", "payment_intent": "pi_test_1",
    }
    session.update(overrides)
    return session


def _post_event(client, kind, obj):
    body, headers = _signed(_event(kind, obj))
    return client.post("/api/payments/webhook", content=body, headers=headers)


def _checkout(client, student, package):
    return client.post(f"/api/payments/checkout/{package.id}", headers=auth_headers(student))


def test_checkout_creates_pending_order_without_granting(client, db, student, catalog, stripe_on):
    response = _checkout(client, student, catalog["package"])
    assert response.status_code == 200
    assert response.json()["checkout_url"].startswith("https://checkout.stripe.com/")

    sent = stripe_on[0]
    assert sent["line_items"][0]["price_data"]["unit_amount"] == 4900
    assert sent["customer_email"] == student.email
    order = db.query(Order).one()
    assert order.status == "pending" and order.stripe_checkout_session_id == "cs_test_1"
    assert db.query(UserPackage).count() == 0


def test_paid_webhook_grants_package_once(client, db, student, catalog, stripe_on):
    _checkout(client, student, catalog["package"])
    for _ in range(2):
        assert _post_event(client, "checkout.session.completed", _paid_session()).status_code == 200

    db.expire_all()
    user_packages = db.query(UserPackage).all()
    assert len(user_packages) == 1
    assert user_packages[0].tests_remaining == catalog["package"].test_count
    order = db.query(Order).one()
    assert order.status == "paid" and order.user_package_id == user_packages[0].id

    orders = client.get("/api/payments/orders", headers=auth_headers(student)).json()
    assert [o["status"] for o in orders] == ["paid"]


def test_webhook_rejects_bad_signature(client, student, catalog, stripe_on):
    _checkout(client, student, catalog["package"])
    body, headers = _signed(_event("checkout.session.completed", _paid_session()), secret="whsec_wrong")
    assert client.post("/api/payments/webhook", content=body, headers=headers).status_code == 400
    assert client.post("/api/payments/webhook", content=body).status_code == 400


@pytest.mark.parametrize("session", [
    _paid_session(payment_status="unpaid"),
    _paid_session(amount=100),
    _paid_session(currency="eur"),
])
def test_unpaid_or_mismatched_session_grants_nothing(client, db, student, catalog, stripe_on, session):
    _checkout(client, student, catalog["package"])
    assert _post_event(client, "checkout.session.completed", session).status_code == 200
    db.expire_all()
    assert db.query(UserPackage).count() == 0
    assert db.query(Order).one().status == "pending"


def test_async_payment_success_grants(client, db, student, catalog, stripe_on):
    _checkout(client, student, catalog["package"])
    _post_event(client, "checkout.session.completed", _paid_session(payment_status="unpaid"))
    _post_event(client, "checkout.session.async_payment_succeeded", _paid_session())
    db.expire_all()
    assert db.query(UserPackage).count() == 1


def test_expired_session_marks_order_expired(client, db, student, catalog, stripe_on):
    _checkout(client, student, catalog["package"])
    _post_event(client, "checkout.session.expired", {"id": "cs_test_1", "object": "checkout.session"})
    db.expire_all()
    assert db.query(Order).one().status == "expired"


def test_full_refund_revokes_credits(client, db, student, catalog, stripe_on):
    _checkout(client, student, catalog["package"])
    _post_event(client, "checkout.session.completed", _paid_session())
    _post_event(client, "charge.refunded", {"id": "ch_1", "object": "charge", "refunded": False, "payment_intent": "pi_test_1"})
    db.expire_all()
    assert db.query(UserPackage).one().tests_remaining > 0

    _post_event(client, "charge.refunded", {"id": "ch_1", "object": "charge", "refunded": True, "payment_intent": "pi_test_1"})
    db.expire_all()
    assert db.query(Order).one().status == "refunded"
    assert db.query(UserPackage).one().tests_remaining == 0
    purchased = client.get("/api/packages/user/purchased", headers=auth_headers(student)).json()
    assert purchased[0]["is_expired"] is True


def test_cannot_buy_package_already_owned(client, db, student, catalog, stripe_on):
    _checkout(client, student, catalog["package"])
    _post_event(client, "checkout.session.completed", _paid_session())
    response = _checkout(client, student, catalog["package"])
    assert response.status_code == 409
    assert _checkout(client, student, catalog["sat_package"]).status_code == 200


def test_checkout_requires_login(client, catalog, stripe_on):
    assert client.post(f"/api/payments/checkout/{catalog['package'].id}").status_code == 401


def test_without_stripe_dev_grants_immediately(client, db, student, catalog):
    response = _checkout(client, student, catalog["package"])
    assert response.status_code == 200
    assert response.json()["checkout_url"] is None
    assert db.query(UserPackage).count() == 1
    assert db.query(Order).count() == 0


def test_without_stripe_or_free_purchase_checkout_is_closed(client, student, catalog, monkeypatch):
    monkeypatch.setattr(config, "ALLOW_FREE_PURCHASE", False)
    assert _checkout(client, student, catalog["package"]).status_code == 503


def test_production_requires_stripe(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://scoreivy.com")
    monkeypatch.setenv("FRONTEND_URL", "https://scoreivy.com")
    try:
        reloaded = importlib.reload(config)
        with pytest.raises(RuntimeError, match="STRIPE_SECRET_KEY"):
            reloaded.validate_settings()
    finally:
        monkeypatch.undo()
        importlib.reload(config)
