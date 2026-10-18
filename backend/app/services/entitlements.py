"""Rules for what a student's purchased packages let them do."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Package, UserPackage


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_aware(value: Optional[datetime]) -> Optional[datetime]:
    """Treat naive datetimes (e.g. from SQLite) as UTC so comparisons don't raise."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def compute_expiry(package: Package, purchased_at: datetime) -> Optional[datetime]:
    if not package.validity_days:
        return None
    return purchased_at + timedelta(days=package.validity_days)


def is_expired(user_package: UserPackage, now: Optional[datetime] = None) -> bool:
    expires_at = as_aware(user_package.expires_at)
    return expires_at is not None and expires_at <= (now or utcnow())


def grant_package(db: Session, user_id: int, package: Package) -> UserPackage:
    """Create the UserPackage for a completed purchase. Caller commits."""
    now = utcnow()
    user_package = UserPackage(
        user_id=user_id,
        package_id=package.id,
        tests_remaining=package.test_count,
        purchased_at=now,
        expires_at=compute_expiry(package, now),
    )
    db.add(user_package)
    return user_package
