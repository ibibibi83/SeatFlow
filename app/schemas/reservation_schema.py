from pydantic import BaseModel
from datetime import datetime
from app.models.reservation import ReservationStatus


class ReservationCreate(BaseModel):
    seats_reserved: int


class ReservationResponse(BaseModel):
    id: int
    user_id: int
    seats_reserved: int
    status: ReservationStatus
    expires_at: datetime

    class Config:
        from_attributes = True