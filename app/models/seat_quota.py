"""
SeatQuota ORM model.

A single row stores the current seat configuration for the venue.
Only operations managers can update it.

total_seats      – physical seats in the restaurant (e.g. 230)
reservable_seats – maximum seats that can be held by active reservations
                   at any point in time (e.g. 50)
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SeatQuota(Base):
    __tablename__ = "seat_quotas"

    id:               Mapped[int]      = mapped_column(Integer, primary_key=True)
    total_seats:      Mapped[int]      = mapped_column(Integer, nullable=False)
    reservable_seats: Mapped[int]      = mapped_column(Integer, nullable=False)
    updated_at:       Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # Username of the staff member who last changed the quota
    updated_by: Mapped[str|None] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:
        return f"<SeatQuota total={self.total_seats} reservable={self.reservable_seats}>"