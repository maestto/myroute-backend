"""Trip activities endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.v1.schemas.activity import (
    TripActivityCreateRequest,
    TripActivityRead,
    TripActivityUpdateRequest,
)
from app.db.models.trip import Trip
from app.db.models.user import User
from app.db.session import get_db
from app.services.activities import (
    create_trip_activity,
    delete_trip_activity,
    list_trip_activities,
    update_trip_activity,
)
from app.services.invites import get_trip_member
from app.services.trips import get_trip_for_user

router = APIRouter(prefix="/trips/{trip_id}/activities")


def _require_trip(db: Session, trip_id: UUID, user: User, *, editing: bool) -> Trip:
    member = get_trip_member(db=db, trip_id=trip_id, user_id=user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if editing and member.role == "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    trip = get_trip_for_user(db=db, trip_id=trip_id, user_id=user.id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


@router.get("", response_model=list[TripActivityRead])
def list_activities(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TripActivityRead]:
    """Return trip activities for members."""
    trip = _require_trip(db, trip_id, current_user, editing=False)
    return [TripActivityRead.model_validate(item) for item in list_trip_activities(db, trip.id)]


@router.post("", response_model=TripActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(
    trip_id: UUID,
    payload: TripActivityCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripActivityRead:
    """Create activity; owner or editor only."""
    trip = _require_trip(db, trip_id, current_user, editing=True)
    try:
        activity = create_trip_activity(db=db, trip=trip, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TripActivityRead.model_validate(activity)


@router.patch("/{activity_id}", response_model=TripActivityRead)
def update_activity(
    trip_id: UUID,
    activity_id: UUID,
    payload: TripActivityUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripActivityRead:
    """Update activity; owner or editor only."""
    trip = _require_trip(db, trip_id, current_user, editing=True)
    try:
        activity = update_trip_activity(db=db, trip=trip, activity_id=activity_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return TripActivityRead.model_validate(activity)


@router.delete("/{activity_id}")
def delete_activity(
    trip_id: UUID,
    activity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete activity; owner or editor only."""
    _require_trip(db, trip_id, current_user, editing=True)
    if not delete_trip_activity(db=db, trip_id=trip_id, activity_id=activity_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return {"status": "deleted"}
