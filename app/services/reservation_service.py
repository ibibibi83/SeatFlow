from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.models.reservation import Reservation, ReservationStatus
from app.models.seat_quota import SeatQuota
from fastapi import HTTPException, status
from app.services.seat_service import SeatService
class ReservationService:

    @staticmethod
    def calculate_reserved_seats(db: Session) -> int:
        stmt = select(func.sum(Reservation.seats_reserved)).where(
            Reservation.status == ReservationStatus.ACTIVE.value,
            Reservation.expires_at > datetime.utcnow()
        )

        result = db.execute(stmt).scalar()
        return result or 0

    @staticmethod
    def calculate_available_seats(db: Session) -> int:
        # Gesamtplätze holen
        quota = SeatService.get_quota(db)


        if not quota:
            return 0

        reserved = ReservationService.calculate_reserved_seats(db)

        return quota.total_seats - reserved

    @staticmethod
    def create_reservation(db: Session, user_id: int, seats: int):

        # 1️ Verfügbare Plätze berechnen
        available = ReservationService.calculate_available_seats(db)
        print(available)
        if seats > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough available seats"
            )

        # 2️ Ablaufzeit setzen (15 Minuten)
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        # 3️ Reservierung erstellen
        reservation = Reservation(
            user_id=user_id,
            seats_reserved=seats,
            status=ReservationStatus.ACTIVE,
            expires_at=expires_at
        )

        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        return reservation