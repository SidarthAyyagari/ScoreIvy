from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import logging
import os
from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import UserResponse
from app.auth import create_access_token

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

router = APIRouter()


def is_skip_admin_auth_enabled() -> bool:
    """True when SKIP_ADMIN_AUTH is set (local dev only)."""
    skip = os.getenv("SKIP_ADMIN_AUTH", "").strip().lower()
    return skip in ("1", "true", "yes")


def resolve_is_admin(email: str) -> bool:
    """Return True if email is listed in ADMIN_EMAILS (comma-separated)."""
    admin_emails = os.getenv("ADMIN_EMAILS", "")
    if not admin_emails.strip():
        return False
    allowed = {e.strip().lower() for e in admin_emails.split(",") if e.strip()}
    return email.lower() in allowed


def sync_user_admin_flag(user: User, db: Session) -> None:
    """Sync is_admin from ADMIN_EMAILS on each login."""
    user.is_admin = resolve_is_admin(user.email)
    db.commit()
    db.refresh(user)


class OAuthLoginRequest(BaseModel):
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    oauth_provider: str = "google"
    oauth_id: Optional[str] = None


@router.post("/oauth-login")
async def oauth_login(
    request: OAuthLoginRequest,
    db: Session = Depends(get_db)
):
    """Create or update user from OAuth login"""
    try:
        logger.info(f"OAuth login attempt for email: {request.email}, provider: {request.oauth_provider}")
        
        # Find or create user
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user:
            logger.info(f"Creating new user for email: {request.email}")
            # Create new user
            user = User(
                email=request.email,
                name=request.name,
                picture=request.picture,
                oauth_provider=request.oauth_provider,
                oauth_id=request.oauth_id,
                last_login_at=datetime.now()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Successfully created user with ID: {user.id}")
        else:
            logger.info(f"Updating existing user with ID: {user.id}")
            # Update existing user with latest OAuth info
            if request.name:
                user.name = request.name
            if request.picture:
                user.picture = request.picture
            if request.oauth_id:
                user.oauth_id = request.oauth_id
            user.oauth_provider = request.oauth_provider
            user.last_login_at = datetime.now()
            db.commit()
            db.refresh(user)
            logger.info(f"Successfully updated user with ID: {user.id}")

        sync_user_admin_flag(user, db)
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        logger.info(f"Successfully generated access token for user ID: {user.id}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "is_admin": user.is_admin,
            }
        }
    except Exception as e:
        logger.error(f"Error in oauth_login: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = authorization.replace("Bearer ", "")
        from app.auth import verify_token
        payload = verify_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")


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

