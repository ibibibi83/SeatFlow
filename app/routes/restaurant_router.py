"""
Seat management routes.

GET   /seats/availability  – public real-time seat availability snapshot
GET   /seats/quota         – full quota details (management only)
PATCH /seats/quota         – update the seat quota (operations manager only)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import ManagementUser, OperationsManagerUser
from app.db.session import get_db
from app.models.seat_quota import SeatQuota
from app.schemas.restaurant_schema import (
    SeatAvailabilityResponse,
    SeatQuotaResponse,
    UpdateQuotaRequest,
)
from app.services.reservation_service import ReservationService
from app.services.seat_service import SeatService

router = APIRouter(prefix="/seats", tags=["Seats"])


def _get_seat_service(db: Annotated[Session, Depends(get_db)]) -> SeatService:
    return SeatService(db)


def _get_reservation_service(db: Annotated[Session, Depends(get_db)]) -> ReservationService:
    return ReservationService(db)


SeatServiceDep        = Annotated[SeatService,        Depends(_get_seat_service)]
ReservationServiceDep = Annotated[ReservationService, Depends(_get_reservation_service)]


@router.get(
    "/availability",
    response_model=SeatAvailabilityResponse,
    summary="Real-time seat availability (public)",
)
def get_availability(
    seat_service:        SeatServiceDep,
    reservation_service: ReservationServiceDep,
) -> SeatAvailabilityResponse:
    """
    Returns how many seats are currently available for reservation.
    No authentication required – displayed to guests before they reserve.
    """
    quota     = seat_service.get_quota()
    snap      = reservation_service.get_availability(quota.reservable_seats)
    return SeatAvailabilityResponse(
        total_seats=quota.total_seats,
        reservable_seats=quota.reservable_seats,
        reserved_seats=snap["reserved_seats"],
        available_seats=snap["available_seats"],
    )


@router.get(
    "/quota",
    response_model=SeatQuotaResponse,
    summary="Full seat quota details (management only)",
)
def get_quota(
    seat_service: SeatServiceDep,
    _:            ManagementUser,
) -> SeatQuotaResponse:
    """Returns the full quota record including who last changed it."""
    quota = seat_service.get_quota()
    return SeatQuotaResponse.model_validate(quota)


@router.patch(
    "/quota",
    response_model=SeatQuotaResponse,
    summary="Update the seat quota (operations manager only)",
)
def update_quota(
    payload:      UpdateQuotaRequest,
    seat_service: SeatServiceDep,
    current_user: OperationsManagerUser,
) -> SeatQuotaResponse:
    """
    Change total_seats and/or reservable_seats.
    Both fields are optional – omit a field to leave it unchanged.
    reservable_seats must not exceed total_seats.
    """
    quota = seat_service.update_quota(
        total_seats=payload.total_seats,
        reservable_seats=payload.reservable_seats,
        updated_by=current_user,
    )
    return SeatQuotaResponse.model_validate(quota)