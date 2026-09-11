from datetime import datetime, timezone

import jwt

from app.services.auth import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
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

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    assert payload["sub"] == "testuser"
    assert payload["role"] == "user"
    assert "exp" in payload


def test_create_access_token_has_future_expiration():
    token = create_access_token("testuser", "user")

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    expiration = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc,
    )

    assert expiration > datetime.now(timezone.utc)
