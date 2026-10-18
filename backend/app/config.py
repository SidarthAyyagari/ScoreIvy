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

# Network slack allowed past a section deadline before answers stop being accepted.
EXAM_SUBMIT_GRACE_SECONDS = int(os.getenv("EXAM_SUBMIT_GRACE_SECONDS", "60"))

# How long a student may stay on a break between sections before the attempt ends.
EXAM_MAX_BREAK_MINUTES = int(os.getenv("EXAM_MAX_BREAK_MINUTES", "60"))


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
        if problems:
            raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))
    else:
        if SECRET_KEY == _DEFAULT_SECRET_KEY:
            logger.warning("SECRET_KEY is the built-in default; set it in backend/.env")
        if not GOOGLE_CLIENT_IDS:
            logger.warning("GOOGLE_CLIENT_ID is not set; Google sign-in will be rejected")
