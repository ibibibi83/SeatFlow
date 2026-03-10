"""
Seat quota service.

Responsible for reading and updating the venue's seat configuration.
All business logic around quota validation lives here so that route
handlers stay thin.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import QuotaExceededException
from app.models.seat_quota import SeatQuota
from app.models.user import User

logger = logging.getLogger(__name__)


class SeatService:
    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_or_create_quota(self) -> SeatQuota:
        """
        Return the single SeatQuota row, creating it with defaults if absent.
        Should never be absent after init_db() runs, but this is a safety net.
        """
        quota = self._db.query(SeatQuota).first()
        if quota is None:
            quota = SeatQuota(
                total_seats=settings.TOTAL_SEATS,
                reservable_seats=settings.RESERVABLE_SEATS,
            )
            self._db.add(quota)
            self._db.commit()
            self._db.refresh(quota)
            logger.warning("SeatQuota was missing – created with defaults.")
        return quota

    # ── Public API ────────────────────────────────────────────────────────────

    def get_quota(self) -> SeatQuota:
        """Return the current seat quota record."""
        return self._get_or_create_quota()

    def get_reservable_seats(self) -> int:
        """Return how many seats can be reserved concurrently."""
        return self._get_or_create_quota().reservable_seats

    def update_quota(
        self,
        total_seats:      int | None,
        reservable_seats: int | None,
        updated_by:       User,
    ) -> SeatQuota:
        """
        Update the seat quota.  Both fields are optional; pass None to leave
        a field unchanged.

        Raises:
            QuotaExceededException: if reservable_seats > total_seats.
        """
        quota = self._get_or_create_quota()

        new_total      = total_seats      if total_seats      is not None else quota.total_seats
        new_reservable = reservable_seats if reservable_seats is not None else quota.reservable_seats

        if new_reservable > new_total:
            raise QuotaExceededException(new_reservable, new_total)

        quota.total_seats      = new_total
        quota.reservable_seats = new_reservable
        quota.updated_at       = datetime.now(tz=timezone.utc)
        quota.updated_by       = updated_by.username

        self._db.commit()
        self._db.refresh(quota)
        logger.info(
            "Seat quota updated by %s: total=%d, reservable=%d",
            updated_by.username, new_total, new_reservable,
        )
        return quota