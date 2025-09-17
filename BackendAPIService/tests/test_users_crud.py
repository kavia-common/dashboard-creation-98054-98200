"""
User CRUD tests: listing, creation with role rules, update, delete permissions and error cases.
"""
from fastapi import status


def test_list_users_requires_auth(client):
    resp = client.get("/users")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_users_as_admin(admin_client):
    resp = admin_client.get("/users")
    assert resp.status_code == 200
    data = resp.json()
    # seeded: admin and user exist
    assert isinstance(data, list)
    emails = [u["email"] for u in data]
    assert "admin@example.com" in emails
    assert "user@example.com" in emails


def test_create_user_as_admin_can_set_role(admin_client):
    payload = {
        "email": "manager@example.com",
        "full_name": "Manager",
        "password": "Manager123!",
        "role": "manager",
    }
    resp = admin_client.post("/users", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    created = resp.json()
    assert created["email"] == payload["email"]
    assert created["role"] == "manager"


def test_create_user_as_non_admin_role_forced_to_user(user_client):
    payload = {
        "email": "someone@example.com",
        "full_name": "Someone",
        "password": "StrongPass1!",
        "role": "admin",  # trying to escalate
    }
    resp = user_client.post("/users", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()
    assert body["email"] == payload["email"]
    assert body["role"] == "user"  # enforced by API


def test_create_user_duplicate_email_returns_400(admin_client):
    payload = {
        "email": "dup@example.com",
        "full_name": "Dup",
        "password": "StrongPass1!",
    }
    r1 = admin_client.post("/users", json=payload)
    assert r1.status_code == status.HTTP_201_CREATED
    r2 = admin_client.post("/users", json=payload)
    assert r2.status_code == 400
    assert r2.json()["detail"] == "Email already exists."


def test_update_user_fullname_and_password(admin_client):
    # Create a user first
    new_user = {
        "email": "editme@example.com",
        "full_name": "Edit Me",
        "password": "Pass123!",
    }
    resp = admin_client.post("/users", json=new_user)
    assert resp.status_code == 201
    user_id = resp.json()["id"]

    # Update full name and password
    update = {"full_name": "Edited Name", "password": "NewPass123!"}
    resp2 = admin_client.put(f"/users/{user_id}", json=update)
    assert resp2.status_code == 200
    assert resp2.json()["full_name"] == "Edited Name"


def test_update_nonexistent_user_returns_404(admin_client):
    resp = admin_client.put("/users/999999", json={"full_name": "Nobody"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found."


def test_delete_user_as_self_allowed(user_client, admin_client):
    # Create a new regular user
    r = admin_client.post(
        "/users",
        json={"email": "selfdel@example.com", "full_name": "Self Del", "password": "Pass123!"},
    )
    assert r.status_code == 201
    user_id = r.json()["id"]

    # Login as that user to get token
    resp_login = admin_client.post(
        "/login",
        json={"email": "selfdel@example.com", "password": "Pass123!"},
    )
    assert resp_login.status_code == 200
    token = resp_login.json()["access_token"]

    # Use a fresh client context to avoid header pollution
    from fastapi.testclient import TestClient
    from src.api.main import app

    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {token}"})
        del_resp = c.delete(f"/users/{user_id}")
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT


def test_delete_user_forbidden_for_other_non_admin(user_client, admin_client):
    # Create victim user
    r = admin_client.post(
        "/users",
        json={"email": "victim@example.com", "full_name": "Victim", "password": "Pass123!"},
    )
    assert r.status_code == 201
    user_id = r.json()["id"]

    # Attempt delete as non-admin different user
    resp = user_client.delete(f"/users/{user_id}")
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert resp.json()["detail"] == "Forbidden."
