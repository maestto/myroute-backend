"""create trip_stops table

Revision ID: 20260305_0004
Revises: 20260305_0003
Create Date: 2026-03-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260305_0004"
down_revision: str | None = "20260305_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trip_stops",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trip_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("location_name", sa.String(length=255), nullable=False),
        sa.Column("date_from", sa.Date(), nullable=True),
        sa.Column("date_to", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint("position > 0", name="ck_trip_stops_position_positive"),
        sa.CheckConstraint(
            "(date_from IS NULL OR date_to IS NULL OR date_to >= date_from)",
            name="ck_trip_stops_dates_valid",
        ),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trip_id", "position", name="uq_trip_stops_trip_position"),
    )
    op.create_index(op.f("ix_trip_stops_trip_id"), "trip_stops", ["trip_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trip_stops_trip_id"), table_name="trip_stops")
    op.drop_table("trip_stops")
