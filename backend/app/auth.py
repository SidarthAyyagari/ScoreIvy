from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

from app.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, GOOGLE_CLIENT_IDS

ALGORITHM = "HS256"


class GoogleTokenError(Exception):
    pass


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_google_credential(credential: str) -> dict:
    """Verify a Google Sign-In ID token and return its claims.

    Checks signature, expiry, issuer, and that the token was minted for one of
    our OAuth client IDs. Raises GoogleTokenError on any failure.
    """
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    if not GOOGLE_CLIENT_IDS:
        raise GoogleTokenError("Google sign-in is not configured")

    try:
        claims = id_token.verify_oauth2_token(credential, google_requests.Request())
    except ValueError as exc:
        raise GoogleTokenError("Invalid Google credential") from exc

    if claims.get("aud") not in GOOGLE_CLIENT_IDS:
        raise GoogleTokenError("Google credential was issued for a different app")
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise GoogleTokenError("Invalid Google credential issuer")
    if not claims.get("email") or not claims.get("email_verified"):
        raise GoogleTokenError("Google account email is not verified")
    return claims
