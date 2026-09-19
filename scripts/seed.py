"""Idempotent demo data seed for local runs and presentations."""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Trip, TripActivity, TripInvite, TripMember, TripStop, User
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
        "activities": [
            (date(2026, 6, 12), time(14, 0), "Заселение в отель", "Адлер", None, "Адлер"),
            (date(2026, 6, 13), time(10, 0), "Олимпийский парк", "Адлер", Decimal("1500"), "Адлер"),
            (date(2026, 6, 14), time(9, 30), "Канатная дорога", "Роза Хутор", Decimal("3200"), "Роза Хутор"),
            (date(2026, 6, 15), time(11, 0), "Треккинг к водопадам", "Роза Хутор", None, "Роза Хутор"),
            (date(2026, 6, 16), time(19, 0), "Ужин в горах", "Роза Хутор", Decimal("4500"), "Роза Хутор"),
            (date(2026, 6, 17), time(12, 0), "Термальный комплекс", "Красная Поляна", Decimal("2500"), "Красная Поляна"),
            (date(2026, 6, 18), time(10, 0), "Дендрарий", "Сочи", Decimal("600"), "Сочи, центр"),
            (date(2026, 6, 19), time(11, 0), "Прогулка по набережной", "Сочи", None, "Сочи, центр"),
        ],
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
        "activities": [
            (date(2026, 10, 2), time(15, 0), "Казанский кремль", "Казань", Decimal("800"), "Казань"),
            (date(2026, 10, 3), time(11, 0), "Улица Баумана", "Казань", None, "Казань"),
            (date(2026, 10, 3), time(19, 0), "Ужин: эчпочмаки и чак-чак", "Казань", Decimal("2000"), "Казань"),
            (date(2026, 10, 4), time(10, 0), "Экскурсия по острову-граду", "Свияжск", Decimal("1500"), "Свияжск"),
            (date(2026, 10, 5), time(12, 0), "Нижегородский кремль", "Нижний Новгород", Decimal("500"), "Нижний Новгород"),
            (date(2026, 10, 5), time(18, 0), "Стрелка на закате", "Нижний Новгород", None, "Нижний Новгород"),
            (date(2026, 10, 6), time(11, 0), "Канатная дорога через Волгу", "Нижний Новгород", Decimal("700"), "Нижний Новгород"),
        ],
    },
]


def _ensure_user(db: Session, email: str, full_name: str) -> User:
    return get_user_by_email(db, email) or create_user(db, email, DEMO_PASSWORD, full_name)


def _ensure_trip(db: Session, spec: dict, users: dict[str, User]) -> None:
    owner = users[spec["owner"]]
    trip = db.scalar(select(Trip).where(Trip.owner_id == owner.id, Trip.title == spec["title"]))
    if trip is None:
        trip = _create_trip(db, spec, users, owner)
    _ensure_activities(db, trip, spec)
    _ensure_invite(db, trip, spec)


def _create_trip(db: Session, spec: dict, users: dict[str, User], owner: User) -> Trip:

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

    db.commit()
    return trip


def _ensure_invite(db: Session, trip: Trip, spec: dict) -> None:
    """Keep the demo invite link valid no matter when the stack was first seeded."""
    if not spec["invite_token"]:
        return
    invite = db.scalar(select(TripInvite).where(TripInvite.token == spec["invite_token"]))
    if invite is None:
        invite = TripInvite(
            trip_id=trip.id,
            created_by_user_id=trip.owner_id,
            token=spec["invite_token"],
            role="editor",
            used_count=0,
        )
        db.add(invite)
    invite.expires_at = datetime.now(UTC) + timedelta(days=365)
    invite.max_uses = 100
    db.commit()


def _ensure_activities(db: Session, trip: Trip, spec: dict) -> None:
    """Add activities once; lets an already seeded database pick up the new entity."""
    has_any = db.scalar(select(TripActivity.id).where(TripActivity.trip_id == trip.id))
    if has_any:
        return
    stops_by_name = {
        stop.location_name: stop
        for stop in db.scalars(select(TripStop).where(TripStop.trip_id == trip.id))
    }
    for activity_date, time_start, title, location, cost, stop_name in spec["activities"]:
        db.add(
            TripActivity(
                trip_id=trip.id,
                stop_id=stops_by_name[stop_name].id if stop_name in stops_by_name else None,
                title=title,
                location=location,
                date=activity_date,
                time_start=time_start,
                cost=cost,
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
