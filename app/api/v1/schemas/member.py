"""Trip member schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

TripRole = Literal["owner", "editor", "viewer"]


class TripMemberAddRequest(BaseModel):
    """Add an already registered user to a trip by email."""

    email: str = Field(min_length=3, max_length=255)
    role: Literal["editor", "viewer"] = "viewer"


class TripMemberRead(BaseModel):
    """Trip member payload."""

    user_id: UUID
    email: str
    full_name: str | None
    role: TripRole
    joined_at: datetime
