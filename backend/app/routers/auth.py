from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import UserResponse
from app.auth import create_access_token

router = APIRouter()


@router.post("/oauth-login")
async def oauth_login(
    email: str,
    name: Optional[str] = None,
    picture: Optional[str] = None,
    oauth_provider: str = "google",
    oauth_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create or update user from OAuth login"""
    # Find or create user
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create new user
        user = User(
            email=email,
            name=name,
            picture=picture,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user with latest OAuth info
        if name:
            user.name = name
        if picture:
            user.picture = picture
        if oauth_id:
            user.oauth_id = oauth_id
        user.oauth_provider = oauth_provider
        db.commit()
        db.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture
        }
    }


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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

