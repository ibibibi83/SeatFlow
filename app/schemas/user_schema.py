"""
Pydantic schemas for user and authentication endpoints.

UserCreate    – body for POST /auth/users  (ops manager creates a staff account)
UserRegister  – body for POST /auth/register (guest self-registration)
UserLogin     – body for POST /auth/login
TokenOut      – response from POST /auth/login
UserResponse  – response model for user data (never returns the hashed password)
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.roles import UserRole


class UserCreate(BaseModel):
    """Request body to create a new staff account."""

    username:  str      = Field(..., min_length=3, max_length=64)
    email:     EmailStr
    full_name: str      = Field(..., min_length=1, max_length=128)
    password:  str      = Field(..., min_length=8)
    role:      UserRole = UserRole.SHIFT_MANAGER


class UserRegister(BaseModel):
    """Request body for guest self-registration."""

    username:  str      = Field(..., min_length=3, max_length=64)
    email:     EmailStr
    full_name: str      = Field(..., min_length=1, max_length=128)
    password:  str      = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Request body for the login endpoint."""

    username: str
    password: str


class TokenOut(BaseModel):
    """JWT response returned after successful login."""

    access_token: str
    token_type:   str = "bearer"


class UserResponse(BaseModel):
    """Safe user representation – never exposes the hashed password."""

    model_config = {"from_attributes": True}

    id:         int
    username:   str
    email:      EmailStr
    full_name:  str
    role:       UserRole
    is_active:  bool
    created_at: datetime