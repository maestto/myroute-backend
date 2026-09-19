"""Trip stop model."""

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TripStop(Base):
    """Route stop inside trip itinerary."""

    __tablename__ = "trip_stops"
    __table_args__ = (
        UniqueConstraint("trip_id", "position", name="uq_trip_stops_trip_position"),
        CheckConstraint("position > 0", name="ck_trip_stops_position_positive"),
        CheckConstraint(
            "(date_from IS NULL OR date_to IS NULL OR date_to >= date_from)",
            name="ck_trip_stops_dates_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
