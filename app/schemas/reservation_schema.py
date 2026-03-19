"""
Pydantic schemas for the reservation endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from app.models.reservation import ReservationStatus


class ReservationCreate(BaseModel):
    guest_name:           str      = Field(..., min_length=2, max_length=128)
    guest_contact:        str      = Field(..., min_length=5, max_length=128)
    seats_reserved:       int      = Field(..., ge=1, le=20)
    notes:                str | None = Field(None, max_length=512)
    reservation_datetime: datetime | None = Field(None, description="Geplante Ankunftszeit. Wenn leer = sofort.")

    @model_validator(mode='after')
    def validate_datetime(self):
        if self.reservation_datetime is not None:
            now = datetime.now(tz=self.reservation_datetime.tzinfo)
            if self.reservation_datetime < now:
                raise ValueError("Reservierungszeit muss in der Zukunft liegen.")
        return self


class CheckInRequest(BaseModel):
    confirmation_code: str = Field(..., min_length=6, max_length=16)


class ReservationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id:                   int
    confirmation_code:    str
    guest_id:             int
    guest_name:           str
    seats_reserved:       int
    status:               ReservationStatus
    reservation_datetime: datetime | None
    reserved_at:          datetime
    expires_at:           datetime
    checked_in_at:        datetime | None
    cancelled_at:         datetime | None
    notes:                str | None