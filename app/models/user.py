"""
User ORM model.

Represents a staff member (shift_manager or operations_manager).
Guests do not need an account – they interact anonymously via
confirmation codes.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.roles import UserRole
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id:              Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    username:        Mapped[str]      = mapped_column(String(64),  unique=True, index=True, nullable=False)
    email:           Mapped[str]      = mapped_column(String(128), unique=True, index=True, nullable=False)
    full_name:       Mapped[str]      = mapped_column(String(128), nullable=False)
    hashed_password: Mapped[str]      = mapped_column(String(256), nullable=False)
    role:            Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="userrole"), default=UserRole.GUEST, nullable=False)
    is_active:       Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
    created_at:      Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # A user (staff member) may own reservations created on behalf of a guest
    reservations: Mapped[list["Reservation"]] = relationship(  # noqa: F821
        "Reservation", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role}>"