def test_login_returns_jwt(client):
    response = client.post("/auth/token", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_rejects_bad_credentials(client):
    response = client.post("/auth/token", data={"username": "testuser", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert {"id", "username", "role", "disabled"} <= body.keys()
    assert body["disabled"] is False


def test_me_requires_token(client):
    response = client.get("/auth/me")
    assert response.status_code in (401, 403)


def test_invalid_token_rejected(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"