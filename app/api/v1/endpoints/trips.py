"""Trips endpoints for FR-04/FR-05."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.v1.schemas.invite import TripInviteCreateRequest, TripInviteRead
from app.api.v1.schemas.member import TripMemberRead
from app.api.v1.schemas.stop import TripStopCreateRequest, TripStopRead, TripStopUpdateRequest
from app.api.v1.schemas.trip import TripCreateRequest, TripDetailRead, TripRead
from app.core.config import settings
from app.db.models.user import User
from app.db.session import get_db
from app.services.invites import (
    create_trip_invite,
    get_trip_member,
    list_trip_members_with_users,
)
from app.services.stops import create_trip_stop, delete_trip_stop, list_trip_stops, update_trip_stop
from app.services.trips import (
    create_trip_for_owner,
    get_trip_budget_spent,
    get_trip_for_user,
    get_trip_members_count,
    list_user_trips,
)

router = APIRouter(prefix="/trips")


@router.get("", response_model=list[TripRead])
def list_trips(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TripRead]:
    """Return trips list for current user."""
    trips = list_user_trips(db=db, user_id=current_user.id, limit=limit, offset=offset)
    return [TripRead.model_validate(trip) for trip in trips]


@router.post("", response_model=TripRead, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripRead:
    """Create a new trip."""
    try:
        trip = create_trip_for_owner(db=db, owner=current_user, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TripRead.model_validate(trip)


@router.get("/{trip_id}", response_model=TripDetailRead)
def get_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripDetailRead:
    """Return trip overview for a member."""
    trip = get_trip_for_user(db=db, trip_id=trip_id, user_id=current_user.id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    return TripDetailRead(
        trip=TripRead.model_validate(trip),
        members_count=get_trip_members_count(db=db, trip_id=trip.id),
        budget_spent=get_trip_budget_spent(db=db, trip_id=trip.id),
    )


@router.get("/{trip_id}/members", response_model=list[TripMemberRead])
def list_trip_members(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TripMemberRead]:
    """Return members of trip for authorized member."""
    current_member = get_trip_member(db=db, trip_id=trip_id, user_id=current_user.id)
    if not current_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    rows = list_trip_members_with_users(db=db, trip_id=trip_id)
    return [
        TripMemberRead(
            user_id=member.user_id,
            email=user.email,
            full_name=user.full_name,
            role=member.role,
            joined_at=member.joined_at,
        )
        for member, user in rows
    ]


@router.post("/{trip_id}/invites", response_model=TripInviteRead, status_code=status.HTTP_201_CREATED)
def create_invite(
    trip_id: UUID,
    payload: TripInviteCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripInviteRead:
    """Create trip invite token for owner."""
    current_member = get_trip_member(db=db, trip_id=trip_id, user_id=current_user.id)
    if not current_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if current_member.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can create invites")

    try:
        invite = create_trip_invite(
            db=db,
            trip_id=trip_id,
            created_by_user_id=current_user.id,
            role=payload.role,
            expires_in_hours=payload.expires_in_hours,
            max_uses=payload.max_uses,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    frontend_base = settings.frontend_base_url.rstrip("/")
    return TripInviteRead(
        token=invite.token,
        invite_url=f"{frontend_base}/invite/{invite.token}",
        role=invite.role,
        expires_at=invite.expires_at,
        max_uses=invite.max_uses,
        used_count=invite.used_count,
    )


@router.get("/{trip_id}/stops", response_model=list[TripStopRead])
def list_stops(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TripStopRead]:
    """Return trip route stops for members."""
    member = get_trip_member(db=db, trip_id=trip_id, user_id=current_user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    stops = list_trip_stops(db=db, trip_id=trip_id)
    return [TripStopRead.model_validate(stop) for stop in stops]


@router.post("/{trip_id}/stops", response_model=TripStopRead, status_code=status.HTTP_201_CREATED)
def create_stop(
    trip_id: UUID,
    payload: TripStopCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripStopRead:
    """Create route stop for trip."""
    member = get_trip_member(db=db, trip_id=trip_id, user_id=current_user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if member.role == "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    try:
        stop = create_trip_stop(db=db, trip_id=trip_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TripStopRead.model_validate(stop)


@router.patch("/{trip_id}/stops/{stop_id}", response_model=TripStopRead)
def update_stop(
    trip_id: UUID,
    stop_id: UUID,
    payload: TripStopUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripStopRead:
    """Update route stop for trip."""
    member = get_trip_member(db=db, trip_id=trip_id, user_id=current_user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if member.role == "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    try:
        stop = update_trip_stop(db=db, trip_id=trip_id, stop_id=stop_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stop not found")
    return TripStopRead.model_validate(stop)


@router.delete("/{trip_id}/stops/{stop_id}")
def delete_stop(
    trip_id: UUID,
    stop_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete route stop for trip."""
    member = get_trip_member(db=db, trip_id=trip_id, user_id=current_user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if member.role == "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    deleted = delete_trip_stop(db=db, trip_id=trip_id, stop_id=stop_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stop not found")
    return {"status": "deleted"}
