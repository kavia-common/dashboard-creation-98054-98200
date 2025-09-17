"""
Pytest configuration and fixtures for FastAPI BackendAPIService tests.

- Overrides the get_db dependency to use an isolated SQLite database per test session.
- Creates tables and seeds test users (admin and user).
- Provides authorized TestClient instances for admin and user flows.
"""
import os
import pytest
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import app and DB/model helpers from the service
from src.api.main import (
    app,
    Base,
    User,
    Report,
    get_db,
    hash_password,
)

TEST_DATABASE_URL = "sqlite:///./test_db.sqlite"  # file-based to persist across client contexts


@pytest.fixture(scope="session", autouse=True)
def _set_env_for_tests():
    """
    Ensure predictable environment for tests.
    Uses a deterministic JWT secret and disables any external DB via DATABASE_URL override.
    """
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["ADMIN_EMAIL"] = "admin_test@example.com"
    os.environ["ADMIN_PASSWORD"] = "Admin123!"
    yield


@pytest.fixture(scope="session")
def test_engine():
    """
    Create a dedicated SQLite engine for tests.
    """
    # For SQLite, check_same_thread False helps within TestClient threads.
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        future=True,
    )
    return engine


@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    """
    Session factory bound to the test engine.
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database(test_engine, TestingSessionLocal):
    """
    Create all tables once per test session and seed initial data.
    """
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Seed initial users and sample reports
    db = TestingSessionLocal()
    try:
        admin = User(
            email="admin@example.com",
            full_name="Admin User",
            password_hash=hash_password("adminpass"),
            role="admin",
        )
        user = User(
            email="user@example.com",
            full_name="Normal User",
            password_hash=hash_password("userpass"),
            role="user",
        )

        db.add_all([admin, user])
        db.commit()
        db.refresh(admin)
        db.refresh(user)

        # Seed 2 reports for user
        r1 = Report(title="Weekly Stats", description="Weekly overview", owner_id=user.id)
        r2 = Report(title="Q1 Revenues", description="Quarterly revenue report", owner_id=user.id)
        db.add_all([r1, r2])
        db.commit()
    finally:
        db.close()
    yield
    # Teardown
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def app_with_overrides(TestingSessionLocal):
    """
    Provide FastAPI app with DB dependency overridden to use the testing session.
    """
    def _get_test_db() -> Generator:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Apply dependency override
    app.dependency_overrides[get_db] = _get_test_db
    return app


@pytest.fixture
def client(app_with_overrides):
    """
    Unauthenticated TestClient.
    """
    with TestClient(app_with_overrides) as c:
        yield c


@pytest.fixture
def admin_token(client) -> str:
    """
    Obtain JWT for admin.
    """
    resp = client.post("/login", json={"email": "admin@example.com", "password": "adminpass"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def user_token(client) -> str:
    """
    Obtain JWT for normal user.
    """
    resp = client.post("/login", json={"email": "user@example.com", "password": "userpass"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def admin_client(client, admin_token):
    """
    Authenticated client as admin.
    """
    client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return client


@pytest.fixture
def user_client(client, user_token):
    """
    Authenticated client as user.
    """
    client.headers.update({"Authorization": f"Bearer {user_token}"})
    return client
