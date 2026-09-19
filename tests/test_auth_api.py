from fastapi.testclient import TestClient

from app.main import app


def test_register_login_me_flow() -> None:
    client = TestClient(app)

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.user@example.com",
            "password": "strong-password-123",
            "full_name": "New User",
        },
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "new.user@example.com"

    duplicate_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.user@example.com",
            "password": "strong-password-123",
        },
    )
    assert duplicate_response.status_code == 409

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "new.user@example.com", "password": "strong-password-123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "new.user@example.com"


def test_login_with_wrong_password_returns_401() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "new.user@example.com", "password": "invalid-password"},
    )
    assert response.status_code == 401

