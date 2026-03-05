"""Invite acceptance endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.v1.schemas.invite import InviteAcceptResponse
from app.db.models.user import User
from app.db.session import get_db
from app.services.invites import accept_trip_invite

router = APIRouter(prefix="/invites")


@router.post("/{token}/accept", response_model=InviteAcceptResponse)
def accept_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InviteAcceptResponse:
    """Accept trip invite for authenticated user."""
    try:
        trip_id, role = accept_trip_invite(db=db, token=token, user_id=current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return InviteAcceptResponse(trip_id=trip_id, role=role)
