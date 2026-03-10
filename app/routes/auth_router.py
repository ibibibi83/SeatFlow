"""
Authentication routes.

POST /auth/login   – exchange credentials for a JWT access token
POST /auth/users   – create a new staff account (operations manager only)
GET  /auth/me      – return the currently authenticated user's profile
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser, OperationsManagerUser
from app.db.session import get_db
from app.schemas.user_schema import TokenOut, UserCreate, UserLogin, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_user_service(db: Annotated[Session, Depends(get_db)]) -> UserService:
    return UserService(db)


UserServiceDep = Annotated[UserService, Depends(_get_user_service)]


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Log in and receive a JWT access token",
)
def login(payload: UserLogin, service: UserServiceDep) -> TokenOut:
    """
    Validate username and password.
    Returns a Bearer token that must be included in the Authorization header
    for all protected endpoints.
    """
    return service.login(payload)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new staff account (operations manager only)",
)
def create_user(
    payload:  UserCreate,
    service:  UserServiceDep,
    _:        OperationsManagerUser,   # enforces role check
) -> UserResponse:
    """
    Only an operations manager can create new accounts.
    The new account can be assigned the shift_manager or operations_manager role.
    """
    return service.create_user(payload)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the currently authenticated user's profile",
)
def get_me(current_user: CurrentUser) -> UserResponse:
    """Requires a valid Bearer token. Returns the caller's profile."""
    return UserResponse.model_validate(current_user)