"""User endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.api.v1.schemas.user import UserRead
from app.db.models.user import User

router = APIRouter(prefix="/users")


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return current authorized user."""
    return UserRead.model_validate(current_user)

