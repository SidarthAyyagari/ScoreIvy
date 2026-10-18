import importlib

import pytest

from app import config
from app.auth import GoogleTokenError
from app.models.models import User


def _fake_verifier(claims):
    def verify(credential):
        if credential != "valid-token":
            raise GoogleTokenError("Invalid Google credential")
        return claims
    return verify


def test_login_rejects_unverified_email_payload(client):
    response = client.post("/api/auth/oauth-login", json={"email": "admin@example.com"})
    assert response.status_code == 422


def test_login_rejects_invalid_google_token(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.verify_google_credential", _fake_verifier({}))
    response = client.post("/api/auth/oauth-login", json={"credential": "forged"})
    assert response.status_code == 401


def test_login_uses_verified_claims(client, db, monkeypatch):
    claims = {"email": "Admin@Example.com", "email_verified": True, "sub": "google-123", "name": "Ad Min"}
    monkeypatch.setattr("app.routers.auth.verify_google_credential", _fake_verifier(claims))

    response = client.post("/api/auth/oauth-login", json={"credential": "valid-token"})

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "admin@example.com"
    assert body["user"]["is_admin"] is True
    assert db.query(User).filter(User.email == "admin@example.com").one().oauth_id == "google-123"


def test_disabled_user_cannot_log_in_or_use_token(client, db, student, monkeypatch):
    from tests.conftest import auth_headers

    headers = auth_headers(student)
    student.is_active = False
    db.commit()

    claims = {"email": student.email, "email_verified": True, "sub": "s"}
    monkeypatch.setattr("app.routers.auth.verify_google_credential", _fake_verifier(claims))
    assert client.post("/api/auth/oauth-login", json={"credential": "valid-token"}).status_code == 403
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_dev_login_disabled_without_skip_flag(client):
    assert client.post("/api/auth/dev-login").status_code == 403


def test_production_rejects_unsafe_settings(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "short")
    monkeypatch.setenv("SKIP_ADMIN_AUTH", "true")
    try:
        reloaded = importlib.reload(config)
        assert reloaded.SKIP_ADMIN_AUTH is False
        assert reloaded.ALLOW_FREE_PURCHASE is False
        assert reloaded.LOAD_SAMPLE_DATA is False
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            reloaded.validate_settings()
    finally:
        monkeypatch.undo()
        importlib.reload(config)
