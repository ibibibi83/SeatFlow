"""
Reservation routes.

POST   /reservations/       – create a reservation (requires login)
POST   /reservations/check-in – guest check-in
GET    /reservations/my     – list own reservations (requires login)
GET    /reservations/       – list all reservations (management)
DELETE /reservations/{id}   – cancel a reservation (guest or management)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import ManagementUser, CurrentUser
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
    "",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a reservation (requires login)",
)
def create_reservation(
    payload:             ReservationCreate,
    reservation_service: ReservationServiceDep,
    seat_service:        SeatServiceDep,
    current_user:        CurrentUser,
) -> ReservationResponse:
    """Reserve seats. guest_id is taken from the JWT token."""
    reservable = seat_service.get_reservable_seats()
    return reservation_service.create_reservation(
        payload,
        reservable,
        current_user.id,
    )


@router.post(
    "/check-in",
    response_model=FireOrderResponse,
    summary="Guest check-in: fire the pre-order and print receipts",
)
def check_in(
    payload:             CheckInRequest,
    reservation_service: ReservationServiceDep,
    order_service:       OrderServiceDep,
    current_user:        CurrentUser,
) -> FireOrderResponse:
    """Check in with confirmation code. Fires the pre-order to kitchen/bar."""
    reservation = reservation_service.check_in(payload.confirmation_code)
    result = order_service.fire_order_on_checkin(reservation.id)
    print_both_receipts(result.kitchen_bon, result.bar_bon)
    return result


# ── WICHTIG: /my muss VOR /{reservation_id} stehen ───────────
@router.get(
    "/my",
    response_model=list[ReservationResponse],
    summary="List my reservations (requires login)",
)
def get_my_reservations(
    reservation_service: ReservationServiceDep,
    current_user:        CurrentUser,
) -> list[ReservationResponse]:
    """Returns all reservations for the logged-in user, newest first."""
    return reservation_service.get_by_guest_id(current_user.id)


@router.get(
    "",
    response_model=list[ReservationResponse],
    summary="List all reservations (management only)",
)
def list_reservations(
    reservation_service: ReservationServiceDep,
    _:                   ManagementUser,
) -> list[ReservationResponse]:
    """Returns all reservations, newest first."""
    return reservation_service.list_all()


@router.delete(
    "/{reservation_id}",
    response_model=ReservationResponse,
    summary="Cancel a reservation (guest or management)",
)
def cancel_reservation(
    reservation_id:      int,
    reservation_service: ReservationServiceDep,
    current_user:        CurrentUser,
) -> ReservationResponse:
    """
    Guests can cancel their own reservations.
    Management can cancel any reservation.
    """
    reservation = reservation_service.get_reservation_by_id(reservation_id)

    # Gast darf nur seine eigene Reservierung stornieren
    from app.core.roles import UserRole
    if current_user.role == UserRole.GUEST and reservation.guest_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only cancel your own reservations.")

    return reservation_service.cancel_reservation(reservation_id)