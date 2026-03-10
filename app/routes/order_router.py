"""
Order routes.

POST  /orders/reservations/{id}  – add or replace a pre-order (public)
GET   /orders/reservations/{id}  – view a pre-order (public)
GET   /orders/active             – kitchen display: active orders (management)
PATCH /orders/{id}/status        – advance the kitchen workflow (management)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import ManagementUser
from app.db.session import get_db
from app.models.order import OrderStatus
from app.schemas.menu_order_schema import CreateOrUpdateOrderRequest, OrderResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


def _get_order_service(db: Annotated[Session, Depends(get_db)]) -> OrderService:
    return OrderService(db)


OrderServiceDep = Annotated[OrderService, Depends(_get_order_service)]


# ── Guest-facing endpoints ─────────────────────────────────────────────────────

@router.post(
    "/reservations/{reservation_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add or replace a pre-order on a reservation (public)",
)
def create_or_update_order(
    reservation_id: int,
    payload:        CreateOrUpdateOrderRequest,
    service:        OrderServiceDep,
) -> OrderResponse:
    """
    Guests can pre-order food and drinks when they reserve a table.

    The order is saved but NOT sent to the kitchen immediately –
    it is fired only when the guest checks in.

    Calling this endpoint again replaces the previous pre-order,
    so guests can change their selection up until check-in.
    """
    return service.create_or_update_order(reservation_id, payload)


@router.get(
    "/reservations/{reservation_id}",
    response_model=OrderResponse,
    summary="View the pre-order for a reservation (public)",
)
def get_order(
    reservation_id: int,
    service:        OrderServiceDep,
) -> OrderResponse:
    """Return the current pre-order attached to the given reservation."""
    return service.get_order_by_reservation(reservation_id)


# ── Management / kitchen endpoints ─────────────────────────────────────────────

@router.get(
    "/active",
    response_model=list[OrderResponse],
    summary="All active orders for the kitchen display (management only)",
)
def list_active_orders(
    service: OrderServiceDep,
    _:       ManagementUser,
) -> list[OrderResponse]:
    """
    Returns orders in FIRED, IN_PREPARATION, and READY status,
    sorted oldest-first so the kitchen processes them in the correct sequence.
    """
    return service.list_active_orders()


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Advance an order through the kitchen workflow (management only)",
)
def update_order_status(
    order_id:   int,
    new_status: OrderStatus,
    service:    OrderServiceDep,
    _:          ManagementUser,
) -> OrderResponse:
    """
    Kitchen workflow transitions:

    FIRED → IN_PREPARATION  (chef starts cooking)
    IN_PREPARATION → READY  (dish is ready to be served)
    READY → SERVED          (guest has received the order)

    Any non-terminal status → CANCELLED
    """
    return service.update_order_status(order_id, new_status)