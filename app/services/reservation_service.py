"""
Reservation service.

Handles the full reservation lifecycle:
  create  – validate seat availability, generate confirmation code, persist
  check_in – transition to CHECKED_IN and fire the pre-order
  cancel  – mark as CANCELLED and release seats
  expire  – batch-expire stale PENDING reservations (called by scheduler)
"""

import logging
import secrets
import string
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    InsufficientSeatsException,
    NotFoundException,
    ReservationAlreadyCheckedInException,
    ReservationExpiredException,
)
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.reservation_schema import ReservationCreate, ReservationResponse

logger = logging.getLogger(__name__)

# Characters used for confirmation codes – easy to read, no ambiguous chars
_CODE_CHARS = string.ascii_uppercase + string.digits


def _generate_code(length: int = 10) -> str:
    """Return a cryptographically random alphanumeric confirmation code."""
    return "".join(secrets.choice(_CODE_CHARS) for _ in range(length))


class ReservationService:
    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _count_reserved_seats(self) -> int:
        """Sum of seats held by currently PENDING reservations."""
        result = (
            self._db.query(func.sum(Reservation.seats_reserved))
            .filter(
                Reservation.status == ReservationStatus.PENDING,
                Reservation.expires_at > datetime.now(tz=timezone.utc),
            )
            .scalar()
        )
        return result or 0

    def _get_reservation_or_404(self, reservation_id: int) -> Reservation:
        r = self._db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if r is None:
            raise NotFoundException("Reservation", reservation_id)
        return r

    def _get_by_code_or_404(self, code: str) -> Reservation:
        r = self._db.query(Reservation).filter(Reservation.confirmation_code == code).first()
        if r is None:
            raise NotFoundException("Reservation", code)
        return r

    # ── Public API ────────────────────────────────────────────────────────────

    def get_availability(self, reservable_seats: int) -> dict:
        """
        Return a snapshot of current seat availability.

        Args:
            reservable_seats: from SeatService.get_reservable_seats()
        """
        reserved  = self._count_reserved_seats()
        available = max(0, reservable_seats - reserved)
        return {"reservable_seats": reservable_seats, "reserved_seats": reserved, "available_seats": available}

    def create_reservation(self, payload: ReservationCreate, reservable_seats: int) -> ReservationResponse:
        """
        Create a new PENDING reservation.

        Raises:
            InsufficientSeatsException: if not enough seats are available.
        """
        reserved  = self._count_reserved_seats()
        available = max(0, reservable_seats - reserved)

        if payload.seats_reserved > available:
            raise InsufficientSeatsException(payload.seats_reserved, available)

        expires_at = datetime.now(tz=timezone.utc) + \
            __import__("datetime").timedelta(minutes=settings.RESERVATION_DURATION_MINUTES)

        # Retry loop in the unlikely event of a code collision
        for _ in range(5):
            code = _generate_code()
            if not self._db.query(Reservation).filter(Reservation.confirmation_code == code).first():
                break

        reservation = Reservation(
            confirmation_code=code,
            guest_name=payload.guest_name,
            guest_contact=payload.guest_contact,
            seats_reserved=payload.seats_reserved,
            expires_at=expires_at,
            notes=payload.notes,
        )
        self._db.add(reservation)
        self._db.commit()
        self._db.refresh(reservation)

        logger.info(
            "Reservation created: code=%s seats=%d expires=%s",
            code, payload.seats_reserved, expires_at.isoformat(),
        )
        return ReservationResponse.model_validate(reservation)

    def check_in(self, confirmation_code: str) -> Reservation:
        """
        Mark a reservation as CHECKED_IN.

        Raises:
            NotFoundException:                  if no reservation matches the code.
            ReservationExpiredException:        if the reservation has expired.
            ReservationAlreadyCheckedInException: if already checked in.
        """
        reservation = self._get_by_code_or_404(confirmation_code)

        if reservation.status == ReservationStatus.EXPIRED:
            raise ReservationExpiredException(reservation.id)
        if reservation.status == ReservationStatus.CHECKED_IN:
            raise ReservationAlreadyCheckedInException(reservation.id)
        if reservation.status == ReservationStatus.CANCELLED:
            raise NotFoundException("Active reservation", confirmation_code)

        # Treat as expired if the window has passed (scheduler may not have run yet)
        if reservation.expires_at < datetime.now(tz=timezone.utc):
            reservation.status = ReservationStatus.EXPIRED
            self._db.commit()
            raise ReservationExpiredException(reservation.id)

        reservation.status        = ReservationStatus.CHECKED_IN
        reservation.checked_in_at = datetime.now(tz=timezone.utc)
        self._db.commit()
        self._db.refresh(reservation)

        logger.info("Reservation %d checked in (code=%s).", reservation.id, confirmation_code)
        return reservation

    def cancel_reservation(self, reservation_id: int) -> ReservationResponse:
        """
        Cancel a PENDING reservation, releasing its seats immediately.

        Raises:
            NotFoundException:   if reservation does not exist.
            ConflictException:   if reservation is not in a cancellable state.
        """
        from app.core.exceptions import ConflictException
        reservation = self._get_reservation_or_404(reservation_id)

        if reservation.status not in (ReservationStatus.PENDING,):
            raise ConflictException(
                f"Cannot cancel a reservation with status '{reservation.status}'."
            )

        reservation.status       = ReservationStatus.CANCELLED
        reservation.cancelled_at = datetime.now(tz=timezone.utc)
        self._db.commit()
        self._db.refresh(reservation)

        logger.info("Reservation %d cancelled.", reservation_id)
        return ReservationResponse.model_validate(reservation)

    def list_all(self) -> list[ReservationResponse]:
        """Return all reservations ordered by creation time (management only)."""
        rows = (
            self._db.query(Reservation)
            .order_by(Reservation.reserved_at.desc())
            .all()
        )
        return [ReservationResponse.model_validate(r) for r in rows]

    def expire_stale_reservations(self) -> int:
        """
        Batch-expire PENDING reservations whose time window has elapsed.

        Called periodically by the background scheduler.
        Returns the number of reservations that were expired.
        """
        now = datetime.now(tz=timezone.utc)
        stale = (
            self._db.query(Reservation)
            .filter(
                Reservation.status == ReservationStatus.PENDING,
                Reservation.expires_at <= now,
            )
            .all()
        )
        for r in stale:
            r.status = ReservationStatus.EXPIRED

        if stale:
            self._db.commit()
        return len(stale)