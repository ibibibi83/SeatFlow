from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from app.db.base import Base


class SeatQuota(Base):
    __tablename__ = "seat_quota"

    id = Column(Integer, primary_key=True, index=True)
    total_seats = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)