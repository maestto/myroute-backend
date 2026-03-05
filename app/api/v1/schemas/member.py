"""Trip member schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

TripRole = Literal["owner", "editor", "viewer"]


class TripMemberRead(BaseModel):
    """Trip member payload."""

    user_id: UUID
    email: str
    full_name: str | None
    role: TripRole
    joined_at: datetime
