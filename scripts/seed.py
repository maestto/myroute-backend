"""Idempotent demo data seed for local runs and presentations."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Trip, TripInvite, TripMember, TripStop, User
from app.db.session import SessionLocal
from app.services.auth import create_user, get_user_by_email

DEMO_PASSWORD = "demo-pass-123"

USERS = [
    ("demo@myroute.dev", "Демо Пользователь"),
    ("ivan@myroute.dev", "Иван Петров"),
    ("olga@myroute.dev", "Ольга Кузнецова"),
    ("anna@myroute.dev", "Анна Смирнова"),
]

TRIPS = [
    {
        "title": "Неделя в Сочи",
        "description": "Море, горы и Олимпийский парк одной поездкой",
        "start_date": date(2026, 6, 12),
        "end_date": date(2026, 6, 19),
        "base_city": "Сочи",
        "currency": "RUB",
        "budget_total": Decimal("120000.00"),
        "owner": "demo@myroute.dev",
        "members": {"ivan@myroute.dev": "editor", "olga@myroute.dev": "viewer"},
        "stops": [
            ("Адлер", date(2026, 6, 12), date(2026, 6, 13), "Заселение, Олимпийский парк"),
            ("Роза Хутор", date(2026, 6, 14), date(2026, 6, 16), "Канатки, треккинг"),
            ("Красная Поляна", date(2026, 6, 17), date(2026, 6, 17), "Термы"),
            ("Сочи, центр", date(2026, 6, 18), date(2026, 6, 19), "Дендрарий, набережная"),
        ],
        "invite_token": "demo-invite-sochi",
    },
    {
        "title": "Казань — Нижний Новгород",
        "description": "Два города за длинные выходные",
        "start_date": date(2026, 10, 2),
        "end_date": date(2026, 10, 6),
        "base_city": "Казань",
        "currency": "RUB",
        "budget_total": Decimal("60000.00"),
        "owner": "ivan@myroute.dev",
        "members": {"demo@myroute.dev": "editor", "anna@myroute.dev": "viewer"},
        "stops": [
            ("Казань", date(2026, 10, 2), date(2026, 10, 4), "Кремль, Баумана"),
            ("Свияжск", date(2026, 10, 4), date(2026, 10, 4), "Остров-град"),
            ("Нижний Новгород", date(2026, 10, 5), date(2026, 10, 6), "Кремль, Стрелка"),
        ],
        "invite_token": None,
    },
]


def _ensure_user(db: Session, email: str, full_name: str) -> User:
    return get_user_by_email(db, email) or create_user(db, email, DEMO_PASSWORD, full_name)


def _ensure_trip(db: Session, spec: dict, users: dict[str, User]) -> None:
    owner = users[spec["owner"]]
    exists = db.scalar(select(Trip).where(Trip.owner_id == owner.id, Trip.title == spec["title"]))
    if exists:
        return

    trip = Trip(
        owner_id=owner.id,
        title=spec["title"],
        description=spec["description"],
        start_date=spec["start_date"],
        end_date=spec["end_date"],
        base_city=spec["base_city"],
        currency=spec["currency"],
        budget_total=spec["budget_total"],
    )
    db.add(trip)
    db.flush()

    db.add(TripMember(trip_id=trip.id, user_id=owner.id, role="owner"))
    for email, role in spec["members"].items():
        db.add(TripMember(trip_id=trip.id, user_id=users[email].id, role=role))

    for position, (name, date_from, date_to, notes) in enumerate(spec["stops"], start=1):
        db.add(
            TripStop(
                trip_id=trip.id,
                position=position,
                location_name=name,
                date_from=date_from,
                date_to=date_to,
                notes=notes,
            )
        )

    if spec["invite_token"]:
        db.add(
            TripInvite(
                trip_id=trip.id,
                created_by_user_id=owner.id,
                token=spec["invite_token"],
                role="editor",
                expires_at=datetime.now(UTC) + timedelta(days=30),
                max_uses=5,
                used_count=0,
            )
        )

    db.commit()


def seed() -> None:
    with SessionLocal() as db:
        users = {email: _ensure_user(db, email, name) for email, name in USERS}
        for spec in TRIPS:
            _ensure_trip(db, spec, users)
    print(f"Seed complete. Demo accounts: {', '.join(e for e, _ in USERS)} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed()
