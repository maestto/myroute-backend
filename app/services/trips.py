"""Trips use-cases."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.schemas.trip import TripCreateRequest
from app.db.models.trip import Trip
from app.db.models.trip_member import TripMember, TripMemberRole
from app.db.models.user import User


def list_user_trips(db: Session, user_id: UUID, limit: int, offset: int) -> list[Trip]:
    """Return trips where user is a member."""
    statement = (
        select(Trip)
        .join(TripMember, Trip.id == TripMember.trip_id)
        .where(TripMember.user_id == user_id)
        .order_by(Trip.start_date.desc(), Trip.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement))


def create_trip_for_owner(db: Session, owner: User, payload: TripCreateRequest) -> Trip:
    """Create trip and owner membership."""
    if payload.end_date < payload.start_date:
        raise ValueError("end_date must be greater than or equal to start_date")
    title = payload.title.strip()
    if not title:
        raise ValueError("title must not be empty")

    trip = Trip(
        owner_id=owner.id,
        title=title,
        description=payload.description.strip() if payload.description else None,
        start_date=payload.start_date,
        end_date=payload.end_date,
        base_city=payload.base_city.strip() if payload.base_city else None,
        currency=payload.currency.upper(),
        budget_total=payload.budget_total,
    )

    db.add(trip)
    db.flush()
    member = TripMember(
        trip_id=trip.id,
        user_id=owner.id,
        role=TripMemberRole.OWNER.value,
    )
    db.add(member)
    db.commit()
    db.refresh(trip)
    return trip


def get_trip_for_user(db: Session, trip_id: UUID, user_id: UUID) -> Trip | None:
    """Return trip if user has access."""
    statement = (
        select(Trip)
        .join(TripMember, Trip.id == TripMember.trip_id)
        .where(Trip.id == trip_id, TripMember.user_id == user_id)
    )
    return db.scalar(statement)


def get_trip_members_count(db: Session, trip_id: UUID) -> int:
    """Count trip members."""
    statement = select(func.count()).select_from(TripMember).where(TripMember.trip_id == trip_id)
    return int(db.scalar(statement) or 0)


def get_trip_budget_spent(db: Session, trip_id: UUID) -> Decimal:
    """Return spent amount placeholder until expenses module is implemented."""
    del db, trip_id
    return Decimal("0.00")
