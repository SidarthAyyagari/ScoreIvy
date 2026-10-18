"""Stripe Checkout for packages. Credits are granted only from the signed webhook."""

import logging
from typing import Optional, Tuple

import stripe
from sqlalchemy.orm import Session

from app import config
from app.models.models import Order, Package, User
from app.services.entitlements import grant_package, is_expired, utcnow

logger = logging.getLogger(__name__)

PENDING, PAID, EXPIRED, REFUNDED = "pending", "paid", "expired", "refunded"


class CheckoutError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def price_in_cents(package: Package) -> int:
    return int(round(package.price * 100))


def ensure_can_buy(db: Session, user: User, package: Package) -> None:
    """Block buying a pack the student still has: with no retakes, a second copy would be unusable."""
    if not package.is_active:
        raise CheckoutError(400, "Package is not available")
    for owned in user.packages:
        if owned.package_id == package.id and not is_expired(owned):
            raise CheckoutError(409, "You already own this package")


def create_checkout(db: Session, user: User, package: Package) -> Tuple[Order, str]:
    """Create a pending Order and its Stripe Checkout Session; returns the order and checkout URL. Caller commits."""
    amount = price_in_cents(package)
    if amount < 50:
        raise CheckoutError(400, "Package price is below the payment minimum")

    order = Order(
        user_id=user.id,
        package_id=package.id,
        status=PENDING,
        amount_cents=amount,
        currency=config.CHECKOUT_CURRENCY,
    )
    db.add(order)
    db.flush()

    session = stripe.checkout.Session.create(
        api_key=config.STRIPE_SECRET_KEY,
        mode="payment",
        customer_email=user.email,
        client_reference_id=str(order.id),
        metadata={"order_id": str(order.id), "user_id": str(user.id), "package_id": str(package.id)},
        line_items=[{
            "quantity": 1,
            "price_data": {
                "currency": order.currency,
                "unit_amount": amount,
                "product_data": {
                    "name": package.name,
                    "description": package.description or f"{package.test_count} practice tests",
                },
            },
        }],
        success_url=f"{config.FRONTEND_URL}/dashboard?checkout=success",
        cancel_url=f"{config.FRONTEND_URL}/dashboard?checkout=cancelled",
    )
    order.stripe_checkout_session_id = session["id"]
    return order, session["url"]


def parse_event(payload: bytes, signature: Optional[str]):
    """Verify the Stripe signature; raises ValueError or stripe.error.SignatureVerificationError."""
    return stripe.Webhook.construct_event(payload, signature or "", config.STRIPE_WEBHOOK_SECRET)


def _order_for_session(db: Session, session) -> Optional[Order]:
    order = (
        db.query(Order)
        .filter(Order.stripe_checkout_session_id == session["id"])
        .with_for_update()
        .first()
    )
    if order is None:
        logger.warning("Stripe session %s has no matching order", session["id"])
    return order


def fulfill(db: Session, session) -> None:
    """Grant the package for a paid Checkout Session. Safe to call repeatedly."""
    if session.get("payment_status") != "paid":
        return
    order = _order_for_session(db, session)
    if order is None or order.status in (PAID, REFUNDED):
        return
    if session.get("amount_total") != order.amount_cents or (session.get("currency") or "").lower() != order.currency:
        logger.error("Stripe session %s amount/currency mismatch for order %s", session["id"], order.id)
        return

    user_package = grant_package(db, order.user_id, order.package)
    db.flush()
    order.user_package_id = user_package.id
    order.status = PAID
    order.paid_at = utcnow()
    order.stripe_payment_intent_id = session.get("payment_intent")
    logger.info("Order %s paid; granted user_package %s", order.id, user_package.id)


def expire(db: Session, session) -> None:
    order = _order_for_session(db, session)
    if order is not None and order.status == PENDING:
        order.status = EXPIRED


def refund(db: Session, charge) -> None:
    """On a full refund, mark the order refunded and remove the remaining credits."""
    if not charge.get("refunded") or not charge.get("payment_intent"):
        return
    order = (
        db.query(Order)
        .filter(Order.stripe_payment_intent_id == charge["payment_intent"])
        .with_for_update()
        .first()
    )
    if order is None or order.status == REFUNDED:
        return
    order.status = REFUNDED
    order.refunded_at = utcnow()
    if order.user_package is not None:
        order.user_package.tests_remaining = 0
        order.user_package.expires_at = order.refunded_at
    logger.info("Order %s refunded; credits revoked", order.id)


def handle_event(db: Session, event) -> None:
    kind = event["type"]
    obj = event["data"]["object"]
    if kind in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        fulfill(db, obj)
    elif kind == "checkout.session.expired":
        expire(db, obj)
    elif kind == "charge.refunded":
        refund(db, obj)
