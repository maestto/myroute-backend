"""create trip_activities table

Revision ID: 20260919_0005
Revises: 20260305_0004
Create Date: 2026-09-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260919_0005"
down_revision: str | None = "20260305_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trip_activities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trip_id", sa.Uuid(), nullable=False),
        sa.Column("stop_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time_start", sa.Time(), nullable=True),
        sa.Column("cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("cost IS NULL OR cost >= 0", name="ck_trip_activities_cost_non_negative"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["stop_id"], ["trip_stops.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trip_activities_trip_id"), "trip_activities", ["trip_id"], unique=False)
    op.create_index(op.f("ix_trip_activities_stop_id"), "trip_activities", ["stop_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trip_activities_stop_id"), table_name="trip_activities")
    op.drop_index(op.f("ix_trip_activities_trip_id"), table_name="trip_activities")
    op.drop_table("trip_activities")
