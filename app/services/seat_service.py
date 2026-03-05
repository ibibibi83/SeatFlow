from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.seat_quota import SeatQuota


class SeatService:

    @staticmethod
    def get_quota(db: Session) -> SeatQuota | None:
        stmt = select(SeatQuota)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def create_initial_quota(db: Session, total_seats: int = 230) -> SeatQuota:
        quota = SeatQuota(total_seats=total_seats)
        db.add(quota)
        db.commit()
        db.refresh(quota)
        return quota

    @staticmethod
    def update_quota(db: Session, total_seats: int) -> SeatQuota:
        quota = SeatService.get_quota(db)

        if not quota:
            quota = SeatService.create_initial_quota(db, total_seats)
            return quota

        quota.total_seats = total_seats
        db.commit()
        db.refresh(quota)

        return quota