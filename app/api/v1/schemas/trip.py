"""Trip schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TripCreateRequest(BaseModel):
    """Payload for trip creation."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date
    end_date: date
    base_city: str | None = Field(default=None, max_length=255)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    budget_total: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class TripUpdateRequest(BaseModel):
    """Partial trip update; only provided fields change."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None
    end_date: date | None = None
    base_city: str | None = Field(default=None, max_length=255)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    budget_total: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class TripRead(BaseModel):
    """Public trip representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    title: str
    description: str | None
    start_date: date
    end_date: date
    base_city: str | None
    currency: str
    budget_total: Decimal | None
    created_at: datetime
    updated_at: datetime


class TripDetailRead(BaseModel):
    """Trip detail payload for overview page."""

    trip: TripRead
    members_count: int
    budget_spent: Decimal
