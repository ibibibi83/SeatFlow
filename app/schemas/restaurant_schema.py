"""
Pydantic schemas for seat quota management endpoints.

SeatAvailabilityResponse – public seat availability snapshot
SeatQuotaResponse        – full quota details (management only)
UpdateQuotaRequest       – body for PATCH /seats/quota
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SeatAvailabilityResponse(BaseModel):
    """Public read-only snapshot of current seat availability."""

    total_seats:      int  # physical seats in the venue
    reservable_seats: int  # maximum that can be reserved at once
    reserved_seats:   int  # currently held by active reservations
    available_seats:  int  # reservable_seats minus reserved_seats


class SeatQuotaResponse(BaseModel):
    """Full quota record – visible to management only."""

    model_config = {"from_attributes": True}

    id:               int
    total_seats:      int
    reservable_seats: int
    updated_at:       datetime
    updated_by:       str | None


class UpdateQuotaRequest(BaseModel):
    """Request body to change the seat quota (operations manager only)."""

    total_seats:      int | None = Field(None, ge=1)
    reservable_seats: int | None = Field(None, ge=1)