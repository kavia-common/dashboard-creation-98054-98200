"""
Tests for charts and dashboard endpoints, including response shape and auth enforcement.
"""
from fastapi import status


def test_charts_requires_auth(client):
    resp = client.get("/charts/data")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_dashboard_requires_auth(client):
    resp = client.get("/dashboard")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_charts_response_shape(user_client):
    resp = user_client.get("/charts/data")
    assert resp.status_code == 200
    data = resp.json()
    assert "line" in data and "bar" in data and "pie" in data
    assert isinstance(data["line"]["labels"], list)
    assert isinstance(data["line"]["datasets"], list)
    assert isinstance(data["bar"]["labels"], list)
    assert isinstance(data["bar"]["datasets"], list)
    assert isinstance(data["pie"]["labels"], list)
    assert isinstance(data["pie"]["datasets"], list)


def test_dashboard_counts_and_recent(user_client, admin_client):
    # Create a couple of new reports as user to affect counts/recent
    user_client.post("/reports", json={"title": "Dash A"})
    user_client.post("/reports", json={"title": "Dash B"})

    resp = admin_client.get("/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert "users_count" in body and "reports_count" in body and "recent_reports" in body
    assert isinstance(body["users_count"], int)
    assert isinstance(body["reports_count"], int)
    assert isinstance(body["recent_reports"], list)
