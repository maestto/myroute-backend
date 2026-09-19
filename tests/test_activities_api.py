from fastapi.testclient import TestClient

from app.main import app


def _auth(client: TestClient, email: str) -> dict[str, str]:
    password = "strong-password-123"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    token = client.post("/api/v1/auth/login", data={"username": email, "password": password}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def _create_trip(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/trips",
        headers=headers,
        json={
            "title": "Activities trip",
            "start_date": "2026-10-01",
            "end_date": "2026-10-05",
            "currency": "RUB",
            "budget_total": "10000.00",
        },
    )
    return response.json()["id"]


def test_activity_crud_and_budget_spent_aggregation() -> None:
    client = TestClient(app)
    owner = _auth(client, "activities.owner@example.com")
    trip_id = _create_trip(client, owner)

    stop_id = client.post(
        f"/api/v1/trips/{trip_id}/stops", headers=owner, json={"location_name": "Kazan"}
    ).json()["id"]

    first = client.post(
        f"/api/v1/trips/{trip_id}/activities",
        headers=owner,
        json={
            "title": "Kremlin tour",
            "location": "Kazan Kremlin",
            "date": "2026-10-02",
            "time_start": "10:30",
            "cost": "1500.00",
            "stop_id": stop_id,
        },
    )
    second = client.post(
        f"/api/v1/trips/{trip_id}/activities",
        headers=owner,
        json={"title": "Dinner", "date": "2026-10-02", "cost": "2500.50"},
    )
    third = client.post(
        f"/api/v1/trips/{trip_id}/activities",
        headers=owner,
        json={"title": "Morning walk", "date": "2026-10-01"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 201
    assert first.json()["stop_id"] == stop_id

    listing = client.get(f"/api/v1/trips/{trip_id}/activities", headers=owner)
    assert [item["title"] for item in listing.json()] == ["Morning walk", "Kremlin tour", "Dinner"]

    detail = client.get(f"/api/v1/trips/{trip_id}", headers=owner)
    assert detail.json()["budget_spent"] == "4000.50"

    updated = client.patch(
        f"/api/v1/trips/{trip_id}/activities/{second.json()['id']}",
        headers=owner,
        json={"cost": "500.00", "notes": "cheaper place"},
    )
    assert updated.status_code == 200
    assert updated.json()["cost"] == "500.00"
    assert client.get(f"/api/v1/trips/{trip_id}", headers=owner).json()["budget_spent"] == "2000.00"

    deleted = client.delete(f"/api/v1/trips/{trip_id}/activities/{first.json()['id']}", headers=owner)
    assert deleted.status_code == 200
    assert client.get(f"/api/v1/trips/{trip_id}", headers=owner).json()["budget_spent"] == "500.00"


def test_activity_outside_trip_dates_returns_400() -> None:
    client = TestClient(app)
    owner = _auth(client, "activities.dates@example.com")
    trip_id = _create_trip(client, owner)

    response = client.post(
        f"/api/v1/trips/{trip_id}/activities",
        headers=owner,
        json={"title": "Too late", "date": "2026-10-06"},
    )
    assert response.status_code == 400
    assert "within trip dates" in response.json()["detail"]


def test_stop_from_another_trip_is_rejected() -> None:
    client = TestClient(app)
    owner = _auth(client, "activities.stops@example.com")
    trip_id = _create_trip(client, owner)
    other_trip_id = _create_trip(client, owner)
    foreign_stop_id = client.post(
        f"/api/v1/trips/{other_trip_id}/stops", headers=owner, json={"location_name": "Elsewhere"}
    ).json()["id"]

    response = client.post(
        f"/api/v1/trips/{trip_id}/activities",
        headers=owner,
        json={"title": "Wrong link", "date": "2026-10-02", "stop_id": foreign_stop_id},
    )
    assert response.status_code == 400


def test_viewer_can_read_but_cannot_modify_activities() -> None:
    client = TestClient(app)
    owner = _auth(client, "activities.owner2@example.com")
    trip_id = _create_trip(client, owner)
    invite_token = client.post(
        f"/api/v1/trips/{trip_id}/invites", headers=owner, json={"role": "viewer"}
    ).json()["token"]
    viewer = _auth(client, "activities.viewer@example.com")
    client.post(f"/api/v1/invites/{invite_token}/accept", headers=viewer)

    assert client.get(f"/api/v1/trips/{trip_id}/activities", headers=viewer).status_code == 200
    forbidden = client.post(
        f"/api/v1/trips/{trip_id}/activities",
        headers=viewer,
        json={"title": "Nope", "date": "2026-10-02"},
    )
    assert forbidden.status_code == 403


def test_outsider_gets_404_for_activities() -> None:
    client = TestClient(app)
    owner = _auth(client, "activities.owner3@example.com")
    trip_id = _create_trip(client, owner)
    outsider = _auth(client, "activities.outsider@example.com")

    assert client.get(f"/api/v1/trips/{trip_id}/activities", headers=outsider).status_code == 404


def test_cost_over_twelve_digits_is_rejected_with_422() -> None:
    client = TestClient(app)
    owner = _auth(client, "activities.overflow@example.com")
    trip_id = _create_trip(client, owner)

    response = client.post(
        f"/api/v1/trips/{trip_id}/activities",
        headers=owner,
        json={"title": "Too expensive", "date": "2026-10-02", "cost": "12345678901.00"},
    )
    assert response.status_code == 422


def test_time_with_timezone_offset_is_rejected() -> None:
    client = TestClient(app)
    owner = _auth(client, "activities.tz@example.com")
    trip_id = _create_trip(client, owner)

    response = client.post(
        f"/api/v1/trips/{trip_id}/activities",
        headers=owner,
        json={"title": "Aware", "date": "2026-10-02", "time_start": "10:30:00+03:00"},
    )
    assert response.status_code == 422


def test_deleting_trip_cascades_to_activities_and_hides_them() -> None:
    from uuid import UUID

    from conftest import TestingSessionLocal
    from sqlalchemy import func, select

    from app.db.models import TripActivity

    client = TestClient(app)
    owner = _auth(client, "activities.cascade@example.com")
    trip_id = _create_trip(client, owner)
    client.post(
        f"/api/v1/trips/{trip_id}/activities",
        headers=owner,
        json={"title": "Doomed", "date": "2026-10-02", "cost": "10.00"},
    )

    assert client.delete(f"/api/v1/trips/{trip_id}", headers=owner).status_code == 200
    assert client.get(f"/api/v1/trips/{trip_id}/activities", headers=owner).status_code == 404
    assert client.delete(f"/api/v1/trips/{trip_id}", headers=owner).status_code == 404

    with TestingSessionLocal() as db:
        remaining = db.scalar(
            select(func.count()).select_from(TripActivity).where(TripActivity.trip_id == UUID(trip_id))
        )
    assert remaining == 0
