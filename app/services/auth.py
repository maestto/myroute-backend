"""Auth use-cases."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db.models.user import User


def normalize_email(email: str) -> str:
    """Normalize email for persistence and lookup."""
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get user by email."""
    normalized_email = normalize_email(email)
    return db.scalar(select(User).where(User.email == normalized_email))


def create_user(db: Session, email: str, password: str, full_name: str | None = None) -> User:
    """Create and persist a new user."""
    user = User(
        email=normalize_email(email),
        full_name=full_name,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate user by email and password."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

