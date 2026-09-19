from fastapi.testclient import TestClient

from app.main import app


def _register_and_login(client: TestClient, email: str, password: str = "strong-password-123") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Invite User"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]


def _create_trip(client: TestClient, token: str, title: str = "Invite Trip") -> str:
    response = client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "start_date": "2026-08-01",
            "end_date": "2026-08-04",
            "currency": "USD",
        },
    )
    return response.json()["id"]


def test_owner_can_create_invite_and_other_user_accepts() -> None:
    client = TestClient(app)
    owner_token = _register_and_login(client, "owner.invite@example.com")
    trip_id = _create_trip(client, owner_token)

    create_invite_response = client.post(
        f"/api/v1/trips/{trip_id}/invites",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "viewer", "expires_in_hours": 24, "max_uses": 2},
    )
    assert create_invite_response.status_code == 201
    invite_token = create_invite_response.json()["token"]
    assert create_invite_response.json()["invite_url"].endswith(invite_token)

    member_token = _register_and_login(client, "member.invite@example.com")
    accept_response = client.post(
        f"/api/v1/invites/{invite_token}/accept",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["trip_id"] == trip_id
    assert accept_response.json()["role"] == "viewer"

    members_response = client.get(
        f"/api/v1/trips/{trip_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert members_response.status_code == 200
    assert len(members_response.json()) == 2


def test_non_owner_cannot_create_invite() -> None:
    client = TestClient(app)
    owner_token = _register_and_login(client, "owner.2@example.com")
    trip_id = _create_trip(client, owner_token, title="Owner Trip")

    invite_response = client.post(
        f"/api/v1/trips/{trip_id}/invites",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "viewer"},
    )
    invite_token = invite_response.json()["token"]

    viewer_token = _register_and_login(client, "viewer.2@example.com")
    client.post(
        f"/api/v1/invites/{invite_token}/accept",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    forbidden_response = client.post(
        f"/api/v1/trips/{trip_id}/invites",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"role": "viewer"},
    )
    assert forbidden_response.status_code == 403


def test_invite_accept_is_idempotent_for_same_user() -> None:
    client = TestClient(app)
    owner_token = _register_and_login(client, "owner.idempotent@example.com")
    trip_id = _create_trip(client, owner_token, title="Idempotent Trip")

    invite_response = client.post(
        f"/api/v1/trips/{trip_id}/invites",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "viewer", "max_uses": 1},
    )
    invite_token = invite_response.json()["token"]

    user_token = _register_and_login(client, "idempotent.user@example.com")
    first_accept = client.post(
        f"/api/v1/invites/{invite_token}/accept",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    second_accept = client.post(
        f"/api/v1/invites/{invite_token}/accept",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert first_accept.status_code == 200
    assert second_accept.status_code == 200


def test_invite_with_exhausted_limit_returns_400_for_another_user() -> None:
    client = TestClient(app)
    owner_token = _register_and_login(client, "owner.limit@example.com")
    trip_id = _create_trip(client, owner_token, title="Limit Trip")

    invite_response = client.post(
        f"/api/v1/trips/{trip_id}/invites",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "viewer", "max_uses": 1},
    )
    invite_token = invite_response.json()["token"]

    first_user_token = _register_and_login(client, "first.limit@example.com")
    second_user_token = _register_and_login(client, "second.limit@example.com")

    first_accept = client.post(
        f"/api/v1/invites/{invite_token}/accept",
        headers={"Authorization": f"Bearer {first_user_token}"},
    )
    second_accept = client.post(
        f"/api/v1/invites/{invite_token}/accept",
        headers={"Authorization": f"Bearer {second_user_token}"},
    )

    assert first_accept.status_code == 200
    assert second_accept.status_code == 400


def test_accept_unknown_invite_returns_404() -> None:
    client = TestClient(app)
    user_token = _register_and_login(client, "unknown.invite@example.com")

    response = client.post(
        "/api/v1/invites/not-exists/accept",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404
