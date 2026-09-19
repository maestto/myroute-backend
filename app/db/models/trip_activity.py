"""Trip activity model."""

import datetime as dt
import uuid
from datetime import UTC
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TripActivity(Base):
    """Planned event inside a trip: visit, excursion, meal, transfer."""

    __tablename__ = "trip_activities"
    __table_args__ = (
        CheckConstraint("cost IS NULL OR cost >= 0", name="ck_trip_activities_cost_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stop_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("trip_stops.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    time_start: Mapped[dt.time | None] = mapped_column(Time, nullable=True)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: dt.datetime.now(UTC),
    )
