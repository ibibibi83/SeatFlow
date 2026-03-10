"""
FastAPI dependency injection helpers.

Provides reusable Depends() callables for authentication and authorization.
Import the type aliases (CurrentUser, ManagementUser, etc.) directly into
route functions to avoid repeating Depends() boilerplate.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidTokenException, UnauthorizedException
from app.core.roles import MANAGEMENT_ROLES, QUOTA_ROLES
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# Bearer token extractor – returns None instead of raising when token is absent
bearer_scheme = HTTPBearer(auto_error=False)


def _get_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict:
    """Extract and decode the Bearer token from the Authorization header."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def get_current_user(
    payload: Annotated[dict, Depends(_get_token_payload)],
    db:      Annotated[Session, Depends(get_db)],
) -> User:
    """
    Resolve the authenticated User from the JWT payload.

    Raises 401 if the user id is missing from the token or the user
    does not exist / has been deactivated.
    """
    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenException()
    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found or inactive.")
    return user


# ── Convenience type aliases ──────────────────────────────────────────────────

CurrentUser = Annotated[User, Depends(get_current_user)]


def require_management(current_user: CurrentUser) -> User:
    """Allow only shift_manager and operations_manager roles."""
    if current_user.role not in MANAGEMENT_ROLES:
        raise UnauthorizedException("Shift manager or operations manager role required.")
    return current_user


def require_ops_manager(current_user: CurrentUser) -> User:
    """Allow only the operations_manager role."""
    if current_user.role not in QUOTA_ROLES:
        raise UnauthorizedException("Operations manager role required.")
    return current_user


ManagementUser        = Annotated[User, Depends(require_management)]
OperationsManagerUser = Annotated[User, Depends(require_ops_manager)]