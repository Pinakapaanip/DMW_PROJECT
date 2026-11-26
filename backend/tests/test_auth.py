import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base, get_db, settings
import main

app = main.app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test_auth.db"
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )
    Base.metadata.create_all(bind=test_engine)
    monkeypatch.setattr(main, "engine", test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, client=("127.0.0.1", 50000)) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    test_engine.dispose()


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_register_login_me_and_logout_flow(client):
    # Register
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "Adarsh_01",
            "email": "Adarsh@Chanakya.edu.in",
            "password": "StrongPassword123!",
            "full_name": "Adarsh Kumar",
        },
    )
    assert reg_res.status_code == 201, reg_res.text
    user_data = reg_res.json()
    assert user_data["username"] == "adarsh_01"
    assert user_data["email"] == "adarsh@chanakya.edu.in"
    assert user_data["full_name"] == "Adarsh Kumar"
    assert "password_hash" not in user_data

    # Duplicate register
    dup_res = client.post(
        "/api/v1/auth/register",
        json={
            "username": "adarsh_01",
            "email": "other@chanakya.edu.in",
            "password": "StrongPassword123!",
        },
    )
    assert dup_res.status_code == 409

    # Login (case-insensitive email)
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": "ADARSH@chanakya.edu.in",
            "password": "StrongPassword123!",
        },
    )
    assert login_res.status_code == 200, login_res.text
    token_data = login_res.json()
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # Access /me with token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "adarsh_01"

    # Logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200

    # Access /me with revoked token fails
    revoked_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert revoked_res.status_code == 401


def test_invalid_credentials_and_unauthorized(client):
    # Unauthenticated /me
    assert client.get("/api/v1/auth/me").status_code == 401

    # Invalid token /me
    assert (
        client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        ).status_code
        == 401
    )

    # Wrong password / unknown user
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@chanakya.edu.in", "password": "wrongpassword"},
        ).status_code
        == 401
    )


def test_dev_login_is_disabled_by_default_and_local_only(client, monkeypatch):
    path = "/api/v1/auth/dev-login"
    assert client.post(path).status_code == 404

    monkeypatch.setattr(settings, "allow_dev_login", True)
    response = client.post(path)
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    profile = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile.status_code == 200
    assert profile.json()["email"] == "local-demo@example.com"

    remote_client = TestClient(app, client=("192.0.2.1", 50000))
    assert remote_client.post(path).status_code == 403
