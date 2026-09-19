from fastapi.testclient import TestClient

from app.main import app


def _register_and_login(client: TestClient, email: str, password: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Trips User"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return login_response.json()["access_token"]


def test_trips_requires_auth() -> None:
    client = TestClient(app)
    response_list = client.get("/api/v1/trips")
    response_create = client.post(
        "/api/v1/trips",
        json={
            "title": "Unauthorized trip",
            "start_date": "2026-03-10",
            "end_date": "2026-03-12",
            "currency": "USD",
        },
    )

    assert response_list.status_code == 401
    assert response_create.status_code == 401


def test_create_list_and_get_trip_flow() -> None:
    client = TestClient(app)
    token = _register_and_login(client, "trips.flow@example.com", "strong-password-123")

    create_response = client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Weekend in Sochi",
            "description": "Family trip",
            "start_date": "2026-06-10",
            "end_date": "2026-06-14",
            "base_city": "Sochi",
            "currency": "EUR",
            "budget_total": "1500.00",
        },
    )
    assert create_response.status_code == 201
    trip_id = create_response.json()["id"]

    list_response = client.get("/api/v1/trips", headers={"Authorization": f"Bearer {token}"})
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == trip_id
    assert list_response.json()[0]["title"] == "Weekend in Sochi"

    detail_response = client.get(f"/api/v1/trips/{trip_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail_response.status_code == 200
    assert detail_response.json()["trip"]["id"] == trip_id
    assert detail_response.json()["members_count"] == 1
    assert detail_response.json()["budget_spent"] == "0.00"


def test_create_trip_with_invalid_dates_returns_400() -> None:
    client = TestClient(app)
    token = _register_and_login(client, "trips.invalid@example.com", "strong-password-123")
    response = client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Invalid dates",
            "start_date": "2026-06-20",
            "end_date": "2026-06-10",
            "currency": "USD",
        },
    )
    assert response.status_code == 400


def test_non_member_cannot_open_trip_detail() -> None:
    client = TestClient(app)

    owner_token = _register_and_login(client, "trips.owner@example.com", "strong-password-123")
    create_response = client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "title": "Owner only trip",
            "start_date": "2026-07-01",
            "end_date": "2026-07-03",
            "currency": "USD",
        },
    )
    trip_id = create_response.json()["id"]

    memberless_user_token = _register_and_login(
        client,
        "trips.outsider@example.com",
        "strong-password-123",
    )
    response = client.get(
        f"/api/v1/trips/{trip_id}",
        headers={"Authorization": f"Bearer {memberless_user_token}"},
    )

    assert response.status_code == 404


def test_owner_can_delete_trip_but_editor_cannot() -> None:
    client = TestClient(app)
    owner_token = _register_and_login(client, "trips.delete.owner@example.com", "strong-password-123")
    create_response = client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "title": "Trip to delete",
            "start_date": "2026-08-01",
            "end_date": "2026-08-02",
            "currency": "USD",
        },
    )
    trip_id = create_response.json()["id"]

    invite_token = client.post(
        f"/api/v1/trips/{trip_id}/invites",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "editor"},
    ).json()["token"]
    editor_token = _register_and_login(client, "trips.delete.editor@example.com", "strong-password-123")
    client.post(f"/api/v1/invites/{invite_token}/accept", headers={"Authorization": f"Bearer {editor_token}"})

    forbidden = client.delete(f"/api/v1/trips/{trip_id}", headers={"Authorization": f"Bearer {editor_token}"})
    assert forbidden.status_code == 403

    deleted = client.delete(f"/api/v1/trips/{trip_id}", headers={"Authorization": f"Bearer {owner_token}"})
    assert deleted.status_code == 200

    gone = client.get(f"/api/v1/trips/{trip_id}", headers={"Authorization": f"Bearer {owner_token}"})
    assert gone.status_code == 404


def _trip_with_stop(client: TestClient, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    trip_id = client.post(
        "/api/v1/trips",
        headers=headers,
        json={"title": "Editable", "start_date": "2026-09-01", "end_date": "2026-09-10", "currency": "USD"},
    ).json()["id"]
    client.post(
        f"/api/v1/trips/{trip_id}/stops",
        headers=headers,
        json={"location_name": "Mid", "date_from": "2026-09-05", "date_to": "2026-09-06"},
    )
    return trip_id


def test_owner_edits_trip_and_dates_cannot_exclude_stops() -> None:
    client = TestClient(app)
    owner_token = _register_and_login(client, "trips.edit.owner@example.com", "strong-password-123")
    headers = {"Authorization": f"Bearer {owner_token}"}
    trip_id = _trip_with_stop(client, owner_token)

    edited = client.patch(
        f"/api/v1/trips/{trip_id}",
        headers=headers,
        json={"title": "  Renamed  ", "currency": "eur", "budget_total": "999.50", "base_city": "Rome"},
    )
    assert edited.status_code == 200
    assert edited.json()["title"] == "Renamed"
    assert edited.json()["currency"] == "EUR"
    assert edited.json()["budget_total"] == "999.50"
    assert edited.json()["base_city"] == "Rome"

    widened = client.patch(f"/api/v1/trips/{trip_id}", headers=headers, json={"end_date": "2026-09-20"})
    assert widened.status_code == 200
    assert widened.json()["end_date"] == "2026-09-20"

    too_narrow = client.patch(f"/api/v1/trips/{trip_id}", headers=headers, json={"end_date": "2026-09-04"})
    assert too_narrow.status_code == 400
    assert "existing stops" in too_narrow.json()["detail"]

    inverted = client.patch(f"/api/v1/trips/{trip_id}", headers=headers, json={"start_date": "2026-09-25"})
    assert inverted.status_code == 400

    unchanged = client.get(f"/api/v1/trips/{trip_id}", headers=headers).json()["trip"]
    assert unchanged["start_date"] == "2026-09-01"
    assert unchanged["end_date"] == "2026-09-20"


def test_editor_cannot_edit_trip() -> None:
    client = TestClient(app)
    owner_token = _register_and_login(client, "trips.edit.owner2@example.com", "strong-password-123")
    trip_id = _trip_with_stop(client, owner_token)
    invite_token = client.post(
        f"/api/v1/trips/{trip_id}/invites",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": "editor"},
    ).json()["token"]
    editor_token = _register_and_login(client, "trips.edit.editor@example.com", "strong-password-123")
    client.post(f"/api/v1/invites/{invite_token}/accept", headers={"Authorization": f"Bearer {editor_token}"})

    response = client.patch(
        f"/api/v1/trips/{trip_id}", headers={"Authorization": f"Bearer {editor_token}"}, json={"title": "Hijack"}
    )
    assert response.status_code == 403
