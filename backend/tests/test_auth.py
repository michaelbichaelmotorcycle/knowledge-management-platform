from datetime import datetime, timezone
from unittest.mock import MagicMock

import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.services.auth import (
    ALGORITHM,
    SECRET_KEY,
    authenticate_user,
    create_access_token,
    get_db,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_verify():
    password = "test-password-123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_create_access_token_contains_expected_claims():
    token = create_access_token("testuser", "user")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["sub"] == "testuser"
    assert payload["role"] == "user"
    assert "exp" in payload


def test_create_access_token_has_future_expiration():
    token = create_access_token("testuser", "user")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    expiration = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    assert expiration > datetime.now(timezone.utc)


def test_login_returns_bearer_token_for_valid_credentials():
    mock_db = MagicMock()
    user = User(
        id=1,
        username="auth_test_user",
        hashed_password=get_password_hash("correct-password"),
        role="user",
        disabled=False,
    )
    mock_db.query.return_value.filter.return_value.first.return_value = user

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.post(
                "/auth/token",
                data={"username": "auth_test_user", "password": "correct-password"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    finally:
        app.dependency_overrides.clear()


def test_login_rejects_invalid_password():
    mock_db = MagicMock()
    user = User(
        id=1,
        username="auth_test_user",
        hashed_password=get_password_hash("correct-password"),
        role="user",
        disabled=False,
    )
    mock_db.query.return_value.filter.return_value.first.return_value = user

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.post(
                "/auth/token",
                data={"username": "auth_test_user", "password": "wrong-password"},
            )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"
    finally:
        app.dependency_overrides.clear()


def test_auth_me_requires_token():
    with TestClient(app) as client:
        response = client.get("/auth/me")
    assert response.status_code == 401


def test_invalid_token_rejected():
    with TestClient(app) as client:
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer garbage"}
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_me_returns_current_user_for_valid_token():
    mock_db = MagicMock()
    user = User(
        id=3,
        username="me_test_user",
        hashed_password=get_password_hash("correct-password"),
        role="user",
        disabled=False,
    )
    mock_db.query.return_value.filter.return_value.first.return_value = user

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    token = create_access_token(user.username, user.role)
    try:
        with TestClient(app) as client:
            response = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        body = response.json()
        assert {"id", "username", "role", "disabled"} <= body.keys()
        assert body["disabled"] is False
    finally:
        app.dependency_overrides.clear()


def test_disabled_user_cannot_authenticate():
    mock_db = MagicMock()
    user = User(
        id=2,
        username="disabled_user",
        hashed_password=get_password_hash("correct-password"),
        role="user",
        disabled=True,
    )
    mock_db.query.return_value.filter.return_value.first.return_value = user

    result = authenticate_user(mock_db, "disabled_user", "correct-password")

    assert result is None