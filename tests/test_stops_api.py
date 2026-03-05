from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_get_db() -> Session:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_module() -> None:
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db


def teardown_module() -> None:
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _register_and_login(client: TestClient, email: str, password: str = "strong-password-123") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Stops User"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]


def _create_trip(client: TestClient, token: str, title: str = "Stops Trip") -> str:
    response = client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "start_date": "2026-10-01",
            "end_date": "2026-10-07",
            "currency": "USD",
        },
    )
    return response.json()["id"]


def _accept_invite_with_role(client: TestClient, trip_id: str, owner_token: str, role: str, email: str) -> str:
    invite_response = client.post(
        f"/api/v1/trips/{trip_id}/invites",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"role": role},
    )
    invite_token = invite_response.json()["token"]
    user_token = _register_and_login(client, email)
    client.post(
        f"/api/v1/invites/{invite_token}/accept",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    return user_token


def test_owner_can_crud_stops_and_order_is_normalized() -> None:
    client = TestClient(app)
    owner_token = _register_and_login(client, "stops.owner@example.com")
    trip_id = _create_trip(client, owner_token)

    first = client.post(
        f"/api/v1/trips/{trip_id}/stops",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"location_name": "Moscow"},
    )
    second = client.post(
        f"/api/v1/trips/{trip_id}/stops",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"location_name": "Kazan"},
    )
    third = client.post(
        f"/api/v1/trips/{trip_id}/stops",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"location_name": "Nizhny Novgorod", "position": 2},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 201

    stops = client.get(
        f"/api/v1/trips/{trip_id}/stops",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert stops.status_code == 200
    assert [item["location_name"] for item in stops.json()] == [
        "Moscow",
        "Nizhny Novgorod",
        "Kazan",
    ]

    third_stop_id = third.json()["id"]
    move_response = client.patch(
        f"/api/v1/trips/{trip_id}/stops/{third_stop_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"position": 3, "notes": "Move to end"},
    )
    assert move_response.status_code == 200
    assert move_response.json()["position"] == 3

    delete_response = client.delete(
        f"/api/v1/trips/{trip_id}/stops/{third_stop_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert delete_response.status_code == 200

    final_stops = client.get(
        f"/api/v1/trips/{trip_id}/stops",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert [item["position"] for item in final_stops.json()] == [1, 2]


def test_viewer_can_read_but_cannot_modify_stops() -> None:
    client = TestClient(app)
    owner_token = _register_and_login(client, "stops.owner.viewer@example.com")
    trip_id = _create_trip(client, owner_token, title="Viewer trip")

    viewer_token = _accept_invite_with_role(
        client,
        trip_id=trip_id,
        owner_token=owner_token,
        role="viewer",
        email="stops.viewer@example.com",
    )

    read_response = client.get(
        f"/api/v1/trips/{trip_id}/stops",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert read_response.status_code == 200

    create_response = client.post(
        f"/api/v1/trips/{trip_id}/stops",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"location_name": "Saint Petersburg"},
    )
    assert create_response.status_code == 403


def test_editor_can_create_stops() -> None:
    client = TestClient(app)
    owner_token = _register_and_login(client, "stops.owner.editor@example.com")
    trip_id = _create_trip(client, owner_token, title="Editor trip")

    editor_token = _accept_invite_with_role(
        client,
        trip_id=trip_id,
        owner_token=owner_token,
        role="editor",
        email="stops.editor@example.com",
    )

    create_response = client.post(
        f"/api/v1/trips/{trip_id}/stops",
        headers={"Authorization": f"Bearer {editor_token}"},
        json={"location_name": "Samara"},
    )
    assert create_response.status_code == 201
    assert create_response.json()["location_name"] == "Samara"


def test_stop_with_invalid_dates_returns_400() -> None:
    client = TestClient(app)
    owner_token = _register_and_login(client, "stops.owner.invalid@example.com")
    trip_id = _create_trip(client, owner_token, title="Invalid dates trip")

    response = client.post(
        f"/api/v1/trips/{trip_id}/stops",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "location_name": "Rostov",
            "date_from": "2026-10-10",
            "date_to": "2026-10-01",
        },
    )
    assert response.status_code == 400
