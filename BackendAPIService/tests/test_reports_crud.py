"""
Report CRUD tests: create, list, filter, update and delete with ownership checks.
"""
from fastapi import status


def test_list_reports_requires_auth(client):
    resp = client.get("/reports")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_report_defaults_to_current_user(user_client):
    resp = user_client.post("/reports", json={"title": "My Report", "description": "desc"})
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()
    assert body["title"] == "My Report"


def test_admin_can_create_report_for_other_owner(admin_client):
    # owner_id to be the seeded normal user (email user@example.com); fetch users list to find id
    ulist = admin_client.get("/users")
    assert ulist.status_code == 200
    users = ulist.json()
    user_id = next(u["id"] for u in users if u["email"] == "user@example.com")

    resp = admin_client.post("/reports", json={"title": "Admin Created", "owner_id": user_id})
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["owner_id"] == user_id


def test_update_report_by_owner_allowed(user_client):
    # create a report
    r = user_client.post("/reports", json={"title": "Will Update", "description": "old"})
    assert r.status_code == 201
    rep_id = r.json()["id"]

    # update as owner
    u = user_client.put(f"/reports/{rep_id}", json={"title": "Updated Title", "description": "new"})
    assert u.status_code == 200
    assert u.json()["title"] == "Updated Title"
    assert u.json()["description"] == "new"


def test_update_report_forbidden_by_other_user(admin_client, user_client):
    # Create a report as user
    r = user_client.post("/reports", json={"title": "User Owned"})
    assert r.status_code == 201
    rep_id = r.json()["id"]

    # Create another non-admin user
    other = admin_client.post(
        "/users", json={"email": "other@example.com", "full_name": "Other", "password": "Pass123!"}
    )
    assert other.status_code == 201

    # Login as this other user
    login = admin_client.post("/login", json={"email": "other@example.com", "password": "Pass123!"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    # Attempt to update report
    from fastapi.testclient import TestClient
    from src.api.main import app

    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {token}"})
        resp = c.put(f"/reports/{rep_id}", json={"title": "Hacked"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.json()["detail"] == "Forbidden."


def test_delete_report_by_owner(user_client):
    r = user_client.post("/reports", json={"title": "To be deleted"})
    assert r.status_code == 201
    rep_id = r.json()["id"]

    d = user_client.delete(f"/reports/{rep_id}")
    assert d.status_code == status.HTTP_204_NO_CONTENT


def test_delete_report_not_found_returns_404(user_client):
    resp = user_client.delete("/reports/999999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"] == "Report not found."


def test_list_reports_with_search_and_pagination(user_client, admin_client):
    # Ensure there are a few reports present
    for i in range(3):
        user_client.post("/reports", json={"title": f"Sales {i}", "description": "Quarterly"})

    # Search
    r = admin_client.get("/reports", params={"q": "Sales"})
    assert r.status_code == 200
    items = r.json()
    assert any("Sales" in it["title"] for it in items)

    # Pagination-ish check with limit
    r2 = admin_client.get("/reports", params={"limit": 2})
    assert r2.status_code == 200
    assert len(r2.json()) <= 2
