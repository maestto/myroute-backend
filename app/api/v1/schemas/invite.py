"""Invite schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

TripRole = Literal["owner", "editor", "viewer"]


class TripInviteCreateRequest(BaseModel):
    """Payload for invite creation."""

    expires_in_hours: int = Field(default=24, ge=1, le=168)
    max_uses: int = Field(default=1, ge=1, le=50)
    role: TripRole = "viewer"


class TripInviteRead(BaseModel):
    """Invite response."""

    token: str
    invite_url: str
    role: TripRole
    expires_at: datetime
    max_uses: int
    used_count: int


class InviteAcceptResponse(BaseModel):
    """Invite acceptance response."""

    trip_id: UUID
    role: TripRole
