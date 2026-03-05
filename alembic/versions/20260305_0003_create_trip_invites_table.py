"""create trip_invites table

Revision ID: 20260305_0003
Revises: 20260305_0002
Create Date: 2026-03-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260305_0003"
down_revision: str | None = "20260305_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trip_invites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trip_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=False),
        sa.Column("used_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('owner', 'editor', 'viewer')", name="ck_trip_invites_role_valid"),
        sa.CheckConstraint("max_uses > 0", name="ck_trip_invites_max_uses_positive"),
        sa.CheckConstraint("used_count >= 0", name="ck_trip_invites_used_count_non_negative"),
        sa.CheckConstraint("used_count <= max_uses", name="ck_trip_invites_used_count_within_limit"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trip_invites_trip_id"), "trip_invites", ["trip_id"], unique=False)
    op.create_index(
        op.f("ix_trip_invites_created_by_user_id"),
        "trip_invites",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(op.f("ix_trip_invites_token"), "trip_invites", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_trip_invites_token"), table_name="trip_invites")
    op.drop_index(op.f("ix_trip_invites_created_by_user_id"), table_name="trip_invites")
    op.drop_index(op.f("ix_trip_invites_trip_id"), table_name="trip_invites")
    op.drop_table("trip_invites")
