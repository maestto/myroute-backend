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
