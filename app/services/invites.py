"""Invites and members use-cases."""

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.trip_invite import TripInvite
from app.db.models.trip_member import TripMember
from app.db.models.user import User


def get_trip_member(db: Session, trip_id: UUID, user_id: UUID) -> TripMember | None:
    """Return membership for user in a trip."""
    statement = select(TripMember).where(TripMember.trip_id == trip_id, TripMember.user_id == user_id)
    return db.scalar(statement)


def list_trip_members_with_users(db: Session, trip_id: UUID) -> list[tuple[TripMember, User]]:
    """Return trip members with user details."""
    statement = (
        select(TripMember, User)
        .join(User, User.id == TripMember.user_id)
        .where(TripMember.trip_id == trip_id)
        .order_by(TripMember.joined_at.asc())
    )
    return list(db.execute(statement).all())


def add_member_by_email(db: Session, trip_id: UUID, email: str, role: str) -> tuple[TripMember, User]:
    """Add a registered user to the trip directly; invites remain for people without an account."""
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        raise LookupError("User with this email is not registered")
    if get_trip_member(db=db, trip_id=trip_id, user_id=user.id):
        raise FileExistsError("User is already a member of this trip")

    member = TripMember(trip_id=trip_id, user_id=user.id, role=role)
    db.add(member)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise FileExistsError("User is already a member of this trip") from exc
    db.refresh(member)
    return member, user


def create_trip_invite(
    db: Session,
    trip_id: UUID,
    created_by_user_id: UUID,
    role: str,
    expires_in_hours: int,
    max_uses: int,
) -> TripInvite:
    """Create invite token for trip."""
    if role == "owner":
        raise ValueError("Invite role cannot be owner")

    invite = TripInvite(
        trip_id=trip_id,
        created_by_user_id=created_by_user_id,
        token=_generate_unique_token(db),
        role=role,
        expires_at=datetime.now(UTC) + timedelta(hours=expires_in_hours),
        max_uses=max_uses,
        used_count=0,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def accept_trip_invite(db: Session, token: str, user_id: UUID) -> tuple[UUID, str]:
    """Accept invite and return trip membership tuple."""
    invite = db.scalar(select(TripInvite).where(TripInvite.token == token).with_for_update())
    if not invite:
        raise LookupError("Invite not found")

    existing_member = get_trip_member(db=db, trip_id=invite.trip_id, user_id=user_id)
    if existing_member:
        return invite.trip_id, existing_member.role

    now = datetime.now(UTC)
    expires_at = invite.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < now or invite.used_count >= invite.max_uses:
        raise ValueError("Invite is expired or exhausted")

    trip_id, role = invite.trip_id, invite.role
    db.add(TripMember(trip_id=trip_id, user_id=user_id, role=role))
    invite.used_count += 1
    try:
        db.commit()
    except IntegrityError:
        # A concurrent accept for the same user already created the membership.
        db.rollback()
        existing_member = get_trip_member(db=db, trip_id=trip_id, user_id=user_id)
        if existing_member:
            return trip_id, existing_member.role
        raise
    return trip_id, role


def _generate_unique_token(db: Session) -> str:
    """Generate unique invitation token."""
    for _ in range(5):
        token = token_urlsafe(24)
        exists = db.scalar(select(TripInvite.id).where(TripInvite.token == token))
        if not exists:
            return token
    raise RuntimeError("Failed to generate unique invite token")
