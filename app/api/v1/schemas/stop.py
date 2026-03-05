"""Trip stop schemas."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TripStopCreateRequest(BaseModel):
    """Payload for stop creation."""

    position: int | None = Field(default=None, ge=1)
    location_name: str = Field(min_length=1, max_length=255)
    date_from: date | None = None
    date_to: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class TripStopUpdateRequest(BaseModel):
    """Payload for stop update."""

    position: int | None = Field(default=None, ge=1)
    location_name: str | None = Field(default=None, min_length=1, max_length=255)
    date_from: date | None = None
    date_to: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class TripStopRead(BaseModel):
    """Public stop representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    position: int
    location_name: str
    date_from: date | None
    date_to: date | None
    notes: str | None
