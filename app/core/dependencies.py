"""
FastAPI dependency helpers.

Provides reusable Depends() callables for authentication and
role-based access control used across all route modules.
"""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidTokenException, UnauthorizedException
from app.core.roles import UserRole
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User


def _get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer"):
        raise InvalidTokenException()

    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    user_id: int | None = payload.get("sub")

    if user_id is None:
        raise InvalidTokenException()

    user = db.get(User, int(user_id))
    if user is None:
        raise InvalidTokenException()

    return user


# ── Public dependency aliases ─────────────────────────────────────────────────

CurrentUser = Annotated[User, Depends(_get_current_user)]


def _require_role(*roles: UserRole):
    def _checker(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise UnauthorizedException()
        return current_user
    return _checker


ManagementUser = Annotated[
    User,
    Depends(_require_role(UserRole.SHIFT_MANAGER, UserRole.OPERATIONS_MANAGER)),
]

OperationsManagerUser = Annotated[
    User,
    Depends(_require_role(UserRole.OPERATIONS_MANAGER)),
]