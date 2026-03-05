"""Auth request/response schemas."""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """Payload for user registration."""

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"

