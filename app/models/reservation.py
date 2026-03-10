"""
Reservation ORM model.

A reservation represents a guest's intention to visit the venue.
It holds a fixed number of seats for RESERVATION_DURATION_MINUTES minutes.
If the guest does not check in before expires_at, the scheduler marks
the reservation as EXPIRED and the seats are released automatically.

Status flow:
    PENDING ──(check-in)──► CHECKED_IN
    PENDING ──(expiry)────► EXPIRED
    PENDING ──(cancel)────► CANCELLED
"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReservationStatus(str, Enum):
    PENDING    = "pending"      # active, guest has not arrived yet
    CHECKED_IN = "checked_in"   # guest has arrived, order fired to kitchen
    EXPIRED    = "expired"      # time window elapsed without check-in
    CANCELLED  = "cancelled"    # explicitly cancelled by staff or guest


class Reservation(Base):
    __tablename__ = "reservations"

    id:                Mapped[int]               = mapped_column(Integer, primary_key=True, index=True)
    confirmation_code: Mapped[str]               = mapped_column(String(16), unique=True, index=True, nullable=False)
    guest_name:        Mapped[str]               = mapped_column(String(128), nullable=False)
    guest_contact:     Mapped[str]               = mapped_column(String(128), nullable=False)  # phone or email
    seats_reserved:    Mapped[int]               = mapped_column(Integer, nullable=False)
    status:            Mapped[ReservationStatus] = mapped_column(
        SAEnum(ReservationStatus, name="reservationstatus"),
        default=ReservationStatus.PENDING,
        nullable=False,
        index=True,
    )
    reserved_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at:    Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    checked_in_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at:  Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes:         Mapped[str|None]      = mapped_column(String(512), nullable=True)

    # Optional link to a staff member who created the reservation on behalf of a guest
    user_id: Mapped[int|None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    user:  Mapped["User|None"]  = relationship("User", back_populates="reservations")   # noqa: F821
    order: Mapped["Order|None"] = relationship("Order", back_populates="reservation", uselist=False)  # noqa: F821

    def __repr__(self) -> str:
        return f"<Reservation id={self.id} code={self.confirmation_code!r} status={self.status}>"