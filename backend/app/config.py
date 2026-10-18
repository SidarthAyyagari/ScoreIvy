"""Environment-driven settings shared across the backend.

``ENV=production`` hard-disables every dev shortcut (dev login, SKIP_ADMIN_AUTH,
free purchases, sample data) regardless of what the other variables say.
"""

import logging
import os
from typing import List

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_DEFAULT_SECRET_KEY = "your-secret-key-change-in-production"


def _flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes")


def _csv(name: str) -> List[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


ENV = os.getenv("ENV", "development").strip().lower()
IS_PRODUCTION = ENV == "production"

SECRET_KEY = os.getenv("SECRET_KEY", _DEFAULT_SECRET_KEY)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(7 * 24 * 60)))

# Comma-separated so the student and admin apps can use different OAuth clients.
GOOGLE_CLIENT_IDS = _csv("GOOGLE_CLIENT_ID")

CORS_ORIGINS = _csv("CORS_ORIGINS") or ["http://localhost:3000", "http://localhost:3001"]
CORS_ORIGINS += _csv("CORS_EXTRA_ORIGINS")

SKIP_ADMIN_AUTH = _flag("SKIP_ADMIN_AUTH") and not IS_PRODUCTION

# Lets the dashboard "Purchase" button grant packages without payment. Dev only;
# Stripe Checkout replaces this before launch.
ALLOW_FREE_PURCHASE = _flag("ALLOW_FREE_PURCHASE", default=True) and not IS_PRODUCTION

LOAD_SAMPLE_DATA = _flag("LOAD_SAMPLE_DATA", default=True) and not IS_PRODUCTION

RATE_LIMIT_ENABLED = _flag("RATE_LIMIT_ENABLED", default=True) or IS_PRODUCTION

# Network slack allowed past a section deadline before answers stop being accepted.
EXAM_SUBMIT_GRACE_SECONDS = int(os.getenv("EXAM_SUBMIT_GRACE_SECONDS", "60"))

# How long a student may stay on a break between sections before the attempt ends.
EXAM_MAX_BREAK_MINUTES = int(os.getenv("EXAM_MAX_BREAK_MINUTES", "60"))

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
CHECKOUT_CURRENCY = os.getenv("CHECKOUT_CURRENCY", "usd").strip().lower()
# Student site origin, used for Stripe Checkout success/cancel redirects.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").strip().rstrip("/")


def payments_enabled() -> bool:
    return bool(STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET)


def validate_settings() -> None:
    """Fail fast on configuration that would be unsafe in production."""
    if IS_PRODUCTION:
        problems = []
        if SECRET_KEY == _DEFAULT_SECRET_KEY or len(SECRET_KEY) < 32:
            problems.append("SECRET_KEY must be set to a random value of at least 32 characters")
        if not GOOGLE_CLIENT_IDS:
            problems.append("GOOGLE_CLIENT_ID must be set")
        if not _csv("CORS_ORIGINS"):
            problems.append("CORS_ORIGINS must list the production frontend origins")
        if _flag("SKIP_ADMIN_AUTH"):
            problems.append("SKIP_ADMIN_AUTH must not be set in production")
        if not payments_enabled():
            problems.append("STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET must be set")
        if not os.getenv("FRONTEND_URL", "").startswith("https://"):
            problems.append("FRONTEND_URL must be the https:// student site origin")
        if problems:
            raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))
    else:
        if SECRET_KEY == _DEFAULT_SECRET_KEY:
            logger.warning("SECRET_KEY is the built-in default; set it in backend/.env")
        if not GOOGLE_CLIENT_IDS:
            logger.warning("GOOGLE_CLIENT_ID is not set; Google sign-in will be rejected")
        if not payments_enabled():
            logger.info("Stripe is not configured; checkout grants packages for free (dev only)")
