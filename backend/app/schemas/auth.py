"""Auth request and response schemas."""

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Request body for creating a new user."""

    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """Request body for logging in an existing user."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response returned after signup or login."""

    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    """Public user fields that are safe to return to the frontend."""

    id: int
    email: EmailStr

    model_config = {"from_attributes": True}
