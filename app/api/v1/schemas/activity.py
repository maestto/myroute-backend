"""Trip activity schemas."""

import datetime as dt
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TripActivityCreateRequest(BaseModel):
    """Payload for activity creation."""

    title: str = Field(min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    date: dt.date
    time_start: dt.time | None = None
    cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    notes: str | None = Field(default=None, max_length=2000)
    stop_id: UUID | None = None

    @field_validator("time_start")
    @classmethod
    def _reject_aware_time(cls, value: dt.time | None) -> dt.time | None:
        if value is not None and value.tzinfo is not None:
            raise ValueError("time_start must be a local time without timezone offset")
        return value


class TripActivityUpdateRequest(BaseModel):
    """Payload for activity update; only provided fields change."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    date: dt.date | None = None
    time_start: dt.time | None = None
    cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    notes: str | None = Field(default=None, max_length=2000)
    stop_id: UUID | None = None

    @field_validator("time_start")
    @classmethod
    def _reject_aware_time(cls, value: dt.time | None) -> dt.time | None:
        if value is not None and value.tzinfo is not None:
            raise ValueError("time_start must be a local time without timezone offset")
        return value


class TripActivityRead(BaseModel):
    """Public activity representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    stop_id: UUID | None
    title: str
    location: str | None
    date: dt.date
    time_start: dt.time | None
    cost: Decimal | None
    notes: str | None
