"""Trip stops use-cases."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas.stop import TripStopCreateRequest, TripStopUpdateRequest
from app.db.models.trip import Trip
from app.db.models.trip_stop import TripStop


def list_trip_stops(db: Session, trip_id) -> list[TripStop]:
    """Return ordered trip stops."""
    statement = (
        select(TripStop)
        .where(TripStop.trip_id == trip_id)
        .order_by(TripStop.position.asc(), TripStop.location_name.asc())
    )
    return list(db.scalars(statement))


def create_trip_stop(db: Session, trip_id, payload: TripStopCreateRequest) -> TripStop:
    """Create trip stop at the requested position, shifting the tail right."""
    _validate_dates(payload.date_from, payload.date_to)
    location_name = payload.location_name.strip()
    if not location_name:
        raise ValueError("location_name must not be empty")

    _lock_trip(db, trip_id)
    stops = list_trip_stops(db=db, trip_id=trip_id)
    requested_position = payload.position or (len(stops) + 1)
    position = min(max(1, requested_position), len(stops) + 1)

    # UNIQUE(trip_id, position) is checked per statement: shift from the tail, one row per flush.
    for stop in reversed([item for item in stops if item.position >= position]):
        stop.position += 1
        db.flush()

    new_stop = TripStop(
        trip_id=trip_id,
        position=position,
        location_name=location_name,
        date_from=payload.date_from,
        date_to=payload.date_to,
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(new_stop)
    db.commit()
    db.refresh(new_stop)
    return new_stop


def update_trip_stop(
    db: Session,
    trip_id,
    stop_id,
    payload: TripStopUpdateRequest,
) -> TripStop | None:
    """Update trip stop and reorder route if needed."""
    _lock_trip(db, trip_id)
    stop = db.scalar(select(TripStop).where(TripStop.id == stop_id, TripStop.trip_id == trip_id))
    if not stop:
        return None

    fields_set = payload.model_fields_set
    if "location_name" in fields_set and payload.location_name is not None:
        location_name = payload.location_name.strip()
        if not location_name:
            raise ValueError("location_name must not be empty")
        stop.location_name = location_name

    if "notes" in fields_set:
        stop.notes = payload.notes.strip() if payload.notes else None

    date_from = stop.date_from
    date_to = stop.date_to
    if "date_from" in fields_set:
        date_from = payload.date_from
        stop.date_from = payload.date_from
    if "date_to" in fields_set:
        date_to = payload.date_to
        stop.date_to = payload.date_to
    _validate_dates(date_from, date_to)

    if "position" in fields_set and payload.position is not None:
        _move_stop(db=db, trip_id=trip_id, stop=stop, requested_position=payload.position)

    db.commit()
    db.refresh(stop)
    return stop


def delete_trip_stop(db: Session, trip_id, stop_id) -> bool:
    """Delete trip stop and close the gap in positions."""
    _lock_trip(db, trip_id)
    stop = db.scalar(select(TripStop).where(TripStop.id == stop_id, TripStop.trip_id == trip_id))
    if not stop:
        return False

    removed_position = stop.position
    db.delete(stop)
    db.flush()

    for affected in list_trip_stops(db=db, trip_id=trip_id):
        if affected.position > removed_position:
            affected.position -= 1
            db.flush()

    db.commit()
    return True


def _move_stop(db: Session, trip_id, stop: TripStop, requested_position: int) -> None:
    """Move stop to a new position without violating the unique (trip_id, position) constraint."""
    others = [item for item in list_trip_stops(db=db, trip_id=trip_id) if item.id != stop.id]
    total = len(others) + 1
    target_position = min(max(1, requested_position), total)
    old_position = stop.position
    if target_position == old_position:
        return

    # Park the moving stop in the only slot guaranteed to be free, then close the gap step by step.
    stop.position = total + 1
    db.flush()

    if target_position > old_position:
        for item in others:
            if old_position < item.position <= target_position:
                item.position -= 1
                db.flush()
    else:
        for item in reversed(others):
            if target_position <= item.position < old_position:
                item.position += 1
                db.flush()

    stop.position = target_position
    db.flush()


def _lock_trip(db: Session, trip_id) -> None:
    """Serialize route mutations of one trip: concurrent shifts would race for the same slots."""
    db.execute(select(Trip.id).where(Trip.id == trip_id).with_for_update())


def _validate_dates(date_from, date_to) -> None:
    """Validate stop date range."""
    if date_from and date_to and date_to < date_from:
        raise ValueError("date_to must be greater than or equal to date_from")
