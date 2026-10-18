from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import os
from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import UserResponse
from app.auth import create_access_token, verify_token, verify_google_credential, GoogleTokenError
from app.config import SKIP_ADMIN_AUTH
from app.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


def is_skip_admin_auth_enabled() -> bool:
    """True when SKIP_ADMIN_AUTH is set outside production (local dev only)."""
    return SKIP_ADMIN_AUTH


def resolve_is_admin(email: str) -> bool:
    """Return True if email is listed in ADMIN_EMAILS (comma-separated)."""
    admin_emails = os.getenv("ADMIN_EMAILS", "")
    if not admin_emails.strip():
        return False
    allowed = {e.strip().lower() for e in admin_emails.split(",") if e.strip()}
    return email.lower() in allowed


def sync_user_admin_flag(user: User, db: Session) -> None:
    """Sync is_admin from ADMIN_EMAILS on each login (dev bypass grants admin)."""
    if is_skip_admin_auth_enabled():
        user.is_admin = True
    else:
        user.is_admin = resolve_is_admin(user.email)
    db.commit()
    db.refresh(user)


def dev_login_email() -> str:
    return os.getenv("DEV_LOGIN_EMAIL", "dev@scoreivy.local").strip() or "dev@scoreivy.local"


def _login_response(user: User) -> dict:
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "is_admin": user.is_admin,
        },
    }


class OAuthLoginRequest(BaseModel):
    """Google Sign-In ID token (the ``credential`` field from Google's callback)."""

    credential: str = Field(..., min_length=1)


@router.post("/oauth-login")
@limiter.limit("20/minute")
async def oauth_login(
    request: Request,
    payload: OAuthLoginRequest,
    db: Session = Depends(get_db)
):
    """Verify a Google ID token server-side, then create or update the user."""
    try:
        claims = verify_google_credential(payload.credential)
    except GoogleTokenError as exc:
        logger.warning("Rejected Google sign-in: %s", exc)
        raise HTTPException(status_code=401, detail=str(exc))

    email = claims["email"].lower()
    google_sub = claims["sub"]

    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        logger.info("Creating new user for Google sign-in")
    elif not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    user.name = claims.get("name") or user.name
    user.picture = claims.get("picture") or user.picture
    user.oauth_provider = "google"
    user.oauth_id = google_sub
    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)

    sync_user_admin_flag(user, db)
    return _login_response(user)


@router.post("/dev-login")
async def dev_login(db: Session = Depends(get_db)):
    """Passwordless dev login (no Google). Only when SKIP_ADMIN_AUTH=true outside production."""
    if not is_skip_admin_auth_enabled():
        raise HTTPException(status_code=403, detail="Dev login is disabled")

    email = dev_login_email()
    logger.warning("Dev login used for %s — disable SKIP_ADMIN_AUTH before production", email)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            name="Dev Admin",
            oauth_provider="dev",
            oauth_id="dev",
            last_login_at=datetime.now(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.last_login_at = datetime.now()
        db.commit()
        db.refresh(user)

    sync_user_admin_flag(user, db)
    return _login_response(user)


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_token(authorization[len("Bearer "):])
    user_id = payload.get("sub") if payload else None
    if user_id is None or not str(user_id).isdigit():
        raise HTTPException(status_code=401, detail="Invalid authentication")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require an authenticated admin user (unless SKIP_ADMIN_AUTH is set for local dev)."""
    if is_skip_admin_auth_enabled():
        return current_user
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user
