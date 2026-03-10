"""
User service.

Handles account creation and login logic.
Password hashing is delegated to app.core.security so this service
never stores or returns plain-text passwords.
"""

import logging

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, InvalidCredentialsException
from app.core.roles import UserRole
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserLogin, TokenOut, UserResponse

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_user(self, payload: UserCreate) -> UserResponse:
        """
        Create a new staff account.

        Raises:
            ConflictException: if the username or email is already registered.
        """
        # Check for duplicate username
        if self._db.query(User).filter(User.username == payload.username).first():
            raise ConflictException(f"Username '{payload.username}' is already taken.")

        # Check for duplicate email
        if self._db.query(User).filter(User.email == payload.email).first():
            raise ConflictException(f"Email '{payload.email}' is already registered.")

        user = User(
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=payload.role,
            is_active=True,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        logger.info("User created: %s (%s)", user.username, user.role)
        return UserResponse.model_validate(user)

    def login(self, payload: UserLogin) -> TokenOut:
        """
        Validate credentials and return a JWT access token.

        Raises:
            InvalidCredentialsException: if username or password does not match.
        """
        user = self._db.query(User).filter(User.username == payload.username).first()
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InvalidCredentialsException()

        token = create_access_token(
            subject=user.id,
            extra_claims={"role": user.role.value, "username": user.username},
        )
        logger.info("User logged in: %s", user.username)
        return TokenOut(access_token=token)