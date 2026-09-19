"""Trip activities use-cases."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas.activity import TripActivityCreateRequest, TripActivityUpdateRequest
from app.db.models.trip import Trip
from app.db.models.trip_activity import TripActivity
from app.db.models.trip_stop import TripStop


def list_trip_activities(db: Session, trip_id: UUID) -> list[TripActivity]:
    """Return activities ordered chronologically; untimed ones go last within a day."""
    statement = (
        select(TripActivity)
        .where(TripActivity.trip_id == trip_id)
        .order_by(
            TripActivity.date.asc(),
            TripActivity.time_start.is_(None),
            TripActivity.time_start.asc(),
            TripActivity.title.asc(),
        )
    )
    return list(db.scalars(statement))


def create_trip_activity(db: Session, trip: Trip, payload: TripActivityCreateRequest) -> TripActivity:
    """Create activity inside trip date range."""
    _validate_date_in_trip(trip, payload.date)
    _validate_stop_belongs_to_trip(db, trip.id, payload.stop_id)

    activity = TripActivity(
        trip_id=trip.id,
        stop_id=payload.stop_id,
        title=_clean_required(payload.title, "title"),
        location=_clean_optional(payload.location),
        date=payload.date,
        time_start=payload.time_start,
        cost=payload.cost,
        notes=_clean_optional(payload.notes),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def update_trip_activity(
    db: Session,
    trip: Trip,
    activity_id: UUID,
    payload: TripActivityUpdateRequest,
) -> TripActivity | None:
    """Apply partial update to activity."""
    activity = db.scalar(
        select(TripActivity).where(TripActivity.id == activity_id, TripActivity.trip_id == trip.id)
    )
    if not activity:
        return None

    fields_set = payload.model_fields_set
    if "title" in fields_set and payload.title is not None:
        activity.title = _clean_required(payload.title, "title")
    if "location" in fields_set:
        activity.location = _clean_optional(payload.location)
    if "date" in fields_set and payload.date is not None:
        _validate_date_in_trip(trip, payload.date)
        activity.date = payload.date
    if "time_start" in fields_set:
        activity.time_start = payload.time_start
    if "cost" in fields_set:
        activity.cost = payload.cost
    if "notes" in fields_set:
        activity.notes = _clean_optional(payload.notes)
    if "stop_id" in fields_set:
        _validate_stop_belongs_to_trip(db, trip.id, payload.stop_id)
        activity.stop_id = payload.stop_id

    db.commit()
    db.refresh(activity)
    return activity


def delete_trip_activity(db: Session, trip_id: UUID, activity_id: UUID) -> bool:
    """Delete activity; returns False when it does not exist in this trip."""
    activity = db.scalar(
        select(TripActivity).where(TripActivity.id == activity_id, TripActivity.trip_id == trip_id)
    )
    if not activity:
        return False
    db.delete(activity)
    db.commit()
    return True


def _validate_date_in_trip(trip: Trip, value) -> None:
    if not trip.start_date <= value <= trip.end_date:
        raise ValueError(
            f"Activity date must be within trip dates ({trip.start_date} — {trip.end_date})"
        )


def _validate_stop_belongs_to_trip(db: Session, trip_id: UUID, stop_id: UUID | None) -> None:
    if stop_id is None:
        return
    exists = db.scalar(select(TripStop.id).where(TripStop.id == stop_id, TripStop.trip_id == trip_id))
    if not exists:
        raise ValueError("Stop does not belong to this trip")


def _clean_required(value: str, field: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field} must not be empty")
    return cleaned


def _clean_optional(value: str | None) -> str | None:
    cleaned = value.strip() if value else ""
    return cleaned or None
