import logging
from typing import List

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app import config
from app.db.database import get_db
from app.limiter import limiter
from app.models.models import Order, Package, User
from app.routers.auth import get_current_user
from app.schemas.schemas import CheckoutResponse, OrderResponse
from app.services import payments
from app.services.entitlements import grant_package

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/checkout/{package_id}", response_model=CheckoutResponse)
@limiter.limit("10/minute")
def start_checkout(
    request: Request,
    package_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start buying a package. Returns the Stripe Checkout URL to redirect to.

    Without Stripe keys (local development only) the package is granted immediately.
    """
    package = db.get(Package, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    try:
        payments.ensure_can_buy(db, current_user, package)
        if config.payments_enabled():
            _, checkout_url = payments.create_checkout(db, current_user, package)
            db.commit()
            return CheckoutResponse(checkout_url=checkout_url)
    except payments.CheckoutError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    except stripe.error.StripeError:
        db.rollback()
        logger.exception("Stripe checkout creation failed for package %s", package_id)
        raise HTTPException(status_code=502, detail="Payment provider is unavailable, please try again")

    if not config.ALLOW_FREE_PURCHASE:
        raise HTTPException(status_code=503, detail="Checkout is not available yet")
    user_package = grant_package(db, current_user.id, package)
    db.commit()
    logger.info("Granted package %s to user %s without payment (dev)", package_id, current_user.id)
    return CheckoutResponse(checkout_url=None, user_package_id=user_package.id)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    if not config.payments_enabled():
        raise HTTPException(status_code=503, detail="Payments are not configured")
    payload = await request.body()
    try:
        event = payments.parse_event(payload, stripe_signature)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        payments.handle_event(db, event)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to process Stripe event %s", event.get("id"))
        raise HTTPException(status_code=500, detail="Webhook processing failed")
    return {"received": True}


@router.get("/orders", response_model=List[OrderResponse])
def my_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Order)
        .filter(Order.user_id == current_user.id, Order.status != payments.PENDING)
        .order_by(Order.created_at.desc())
        .all()
    )
