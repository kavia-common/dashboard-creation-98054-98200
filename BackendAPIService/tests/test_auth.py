"""
Auth endpoint tests including JWT, validation errors, and protected access checks.
"""
import jwt
from fastapi import status


def test_health_check(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Healthy"}


def test_login_success(client):
    resp = client.post("/login", json={"email": "admin@example.com", "password": "adminpass"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data and data["token_type"] == "bearer"
    # Ensure token decodes with HS256 (header presence), but not verifying signature here
    token = data["access_token"]
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"


def test_login_invalid_credentials(client):
    resp = client.post("/login", json={"email": "admin@example.com", "password": "wrong"})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert resp.json()["detail"] == "Invalid credentials."


def test_login_validation_error_short_password(client):
    resp = client.post("/login", json={"email": "admin@example.com", "password": "123"})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_protected_requires_auth(client):
    resp = client.get("/users")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in resp.json()


def test_invalid_token_is_rejected(client):
    client.headers.update({"Authorization": "Bearer invalid.token.value"})
    resp = client.get("/users")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert resp.json()["detail"] in ("Invalid token.", "Not authenticated.")
