"""
Pydantic schemas for the reservation endpoints.

ReservationCreate   – body for POST /reservations/
CheckInRequest      – body for POST /reservations/check-in
ReservationResponse – standard reservation response
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.reservation import ReservationStatus


class ReservationCreate(BaseModel):
    """Request body to create a new reservation."""

    guest_name:     str = Field(..., min_length=2, max_length=128, examples=["Maria Schmidt"])
    guest_contact:  str = Field(..., min_length=5, max_length=128, examples=["+49 40 12345678"])
    seats_reserved: int = Field(..., ge=1, le=20)
    notes:          str | None = Field(None, max_length=512, examples=["Window table preferred"])


class CheckInRequest(BaseModel):
    """Request body for the check-in endpoint."""

    confirmation_code: str = Field(..., min_length=6, max_length=16)


class ReservationResponse(BaseModel):
    """Full reservation representation returned to clients."""

    model_config = {"from_attributes": True}

    id:                int
    confirmation_code: str
    guest_name:        str
    guest_contact:     str
    seats_reserved:    int
    status:            ReservationStatus
    reserved_at:       datetime
    expires_at:        datetime
    checked_in_at:     datetime | None
    cancelled_at:      datetime | None
    notes:             str | None