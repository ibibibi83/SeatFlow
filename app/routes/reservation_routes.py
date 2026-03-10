"""
Reservation routes.

POST /reservations/          – create a reservation (public)
POST /reservations/check-in  – guest check-in; fires the pre-order (public)
GET  /reservations/          – list all reservations (management)
DELETE /reservations/{id}    – cancel a reservation (management)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import ManagementUser
from app.db.session import get_db
from app.schemas.menu_order_schema import FireOrderResponse
from app.schemas.reservation_schema import (
    CheckInRequest,
    ReservationCreate,
    ReservationResponse,
)
from app.services.order_service import OrderService
from app.services.printer_service import print_both_receipts
from app.services.reservation_service import ReservationService
from app.services.seat_service import SeatService

router = APIRouter(prefix="/reservations", tags=["Reservations"])


def _get_reservation_service(db: Annotated[Session, Depends(get_db)]) -> ReservationService:
    return ReservationService(db)


def _get_order_service(db: Annotated[Session, Depends(get_db)]) -> OrderService:
    return OrderService(db)


def _get_seat_service(db: Annotated[Session, Depends(get_db)]) -> SeatService:
    return SeatService(db)


ReservationServiceDep = Annotated[ReservationService, Depends(_get_reservation_service)]
OrderServiceDep       = Annotated[OrderService,       Depends(_get_order_service)]
SeatServiceDep        = Annotated[SeatService,        Depends(_get_seat_service)]


@router.post(
    "/",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a reservation (public)",
)
def create_reservation(
    payload:             ReservationCreate,
    reservation_service: ReservationServiceDep,
    seat_service:        SeatServiceDep,
) -> ReservationResponse:
    """
    Reserve seats for an incoming guest.
    The reservation is active for RESERVATION_DURATION_MINUTES minutes.
    After that the scheduler will expire it and release the seats.
    """
    reservable = seat_service.get_reservable_seats()
    return reservation_service.create_reservation(payload, reservable)


@router.post(
    "/check-in",
    response_model=FireOrderResponse,
    summary="Guest check-in: fire the pre-order and print receipts (public)",
)
def check_in(
    payload:             CheckInRequest,
    reservation_service: ReservationServiceDep,
    order_service:       OrderServiceDep,
) -> FireOrderResponse:
    """
    Mark the reservation as CHECKED_IN using the confirmation code.

    If the guest submitted a pre-order, it is immediately fired:
    - Status changes from PENDING_CHECKIN to FIRED
    - A kitchen receipt is generated for food items
    - A bar receipt is generated for beverage items
    Both receipts are returned in the response and logged as if printed.
    """
    # 1. Validate and check in the reservation
    reservation = reservation_service.check_in(payload.confirmation_code)

    # 2. Fire any pre-order attached to this reservation
    result = order_service.fire_order_on_checkin(reservation.id)

    # 3. Send receipts to the printer (logs them; replace with real printer call)
    print_both_receipts(result.kitchen_bon, result.bar_bon)

    return result


@router.get(
    "/",
    response_model=list[ReservationResponse],
    summary="List all reservations (management only)",
)
def list_reservations(
    reservation_service: ReservationServiceDep,
    _:                   ManagementUser,
) -> list[ReservationResponse]:
    """Returns all reservations ordered by creation time, newest first."""
    return reservation_service.list_all()


@router.delete(
    "/{reservation_id}",
    response_model=ReservationResponse,
    summary="Cancel a reservation (management only)",
)
def cancel_reservation(
    reservation_id:      int,
    reservation_service: ReservationServiceDep,
    _:                   ManagementUser,
) -> ReservationResponse:
    """
    Cancel a PENDING reservation and immediately release its seats.
    Cannot be used on already expired or checked-in reservations.
    """
    return reservation_service.cancel_reservation(reservation_id)