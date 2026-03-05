"""Trip stops use-cases."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas.stop import TripStopCreateRequest, TripStopUpdateRequest
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
    """Create trip stop and preserve route ordering."""
    stops = list_trip_stops(db=db, trip_id=trip_id)
    requested_position = payload.position or (len(stops) + 1)
    position = min(max(1, requested_position), len(stops) + 1)

    for stop in reversed(stops):
        if stop.position >= position:
            stop.position += 1

    _validate_dates(payload.date_from, payload.date_to)
    location_name = payload.location_name.strip()
    if not location_name:
        raise ValueError("location_name must not be empty")

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

    if "position" in fields_set and payload.position is not None and payload.position != stop.position:
        _move_stop(db=db, trip_id=trip_id, stop=stop, requested_position=payload.position)

    db.commit()
    db.refresh(stop)
    return stop


def delete_trip_stop(db: Session, trip_id, stop_id) -> bool:
    """Delete trip stop and normalize positions."""
    stop = db.scalar(select(TripStop).where(TripStop.id == stop_id, TripStop.trip_id == trip_id))
    if not stop:
        return False

    removed_position = stop.position
    db.delete(stop)

    for affected in list_trip_stops(db=db, trip_id=trip_id):
        if affected.position > removed_position:
            affected.position -= 1

    db.commit()
    return True


def _move_stop(db: Session, trip_id, stop: TripStop, requested_position: int) -> None:
    """Reorder stop position without breaking unique constraints."""
    total = len(list_trip_stops(db=db, trip_id=trip_id))
    target_position = min(max(1, requested_position), total)
    if target_position == stop.position:
        return

    old_position = stop.position
    stop.position = 0
    db.flush()

    stops = list_trip_stops(db=db, trip_id=trip_id)
    if target_position > old_position:
        for item in stops:
            if old_position < item.position <= target_position:
                item.position -= 1
    else:
        for item in reversed(stops):
            if target_position <= item.position < old_position:
                item.position += 1

    stop.position = target_position


def _validate_dates(date_from, date_to) -> None:
    """Validate stop date range."""
    if date_from and date_to and date_to < date_from:
        raise ValueError("date_to must be greater than or equal to date_from")
