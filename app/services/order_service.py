"""
Order service.

Manages the guest pre-order lifecycle and the kitchen/bar receipt workflow.

Pre-order flow:
  1. Guest creates a reservation  → POST /reservations/
  2. Guest browses the menu       → GET  /menu
  3. Guest submits a pre-order    → POST /orders/reservations/{id}
  4. Guest checks in              → POST /reservations/check-in
     └─ order status PENDING_CHECKIN → FIRED
     └─ kitchen receipt and bar receipt are generated and returned

Kitchen workflow (management):
  FIRED → IN_PREPARATION → READY → SERVED
  Any non-terminal status → CANCELLED
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.models.menu_item import MenuItem, MenuItemType
from app.models.order import Order, OrderItem, OrderStatus
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.menu_order_schema import (
    BonItemLine,
    CreateOrUpdateOrderRequest,
    FireOrderResponse,
    KitchenBon,
    OrderItemResponse,
    OrderResponse,
)

logger = logging.getLogger(__name__)


# ── Private helpers ───────────────────────────────────────────────────────────

def _order_to_response(order: Order) -> OrderResponse:
    """Convert an Order ORM object to its Pydantic response schema."""
    return OrderResponse(
        id=order.id,
        reservation_id=order.reservation_id,
        status=order.status.value,
        total_amount=float(order.total_amount),
        special_requests=order.special_requests,
        fired_at=order.fired_at,
        created_at=order.created_at,
        items=[
            OrderItemResponse(
                id=i.id,
                menu_item_id=i.menu_item_id,
                item_name=i.item_name,
                quantity=i.quantity,
                unit_price=float(i.unit_price),
                subtotal=i.subtotal,
                item_notes=i.item_notes,
            )
            for i in order.items
        ],
    )


def _build_receipt(
    order:             Order,
    reservation:       Reservation,
    item_type_filter:  MenuItemType,
    bon_suffix:        str,
    bon_label:         str,
) -> KitchenBon | None:
    """
    Build a kitchen or bar receipt for one item type.

    Returns None if the order contains no items of the given type
    (e.g. a drinks-only order has no kitchen receipt).

    Args:
        order:            The fired order.
        reservation:      The associated reservation (provides guest info).
        item_type_filter: MenuItemType.FOOD or MenuItemType.BEVERAGE.
        bon_suffix:       "K" for kitchen, "B" for bar.
        bon_label:        "KITCHEN" or "BAR".
    """
    filtered = [i for i in order.items if i.menu_item.item_type == item_type_filter]
    if not filtered:
        return None  # no receipt needed for this station

    food_total = sum(i.subtotal for i in order.items if i.menu_item.item_type == MenuItemType.FOOD)
    bev_total  = sum(i.subtotal for i in order.items if i.menu_item.item_type == MenuItemType.BEVERAGE)

    return KitchenBon(
        bon_number=f"BON-{order.id:04d}-{bon_suffix}",
        bon_type=bon_label,
        reservation_id=reservation.id,
        confirmation_code=reservation.confirmation_code,
        guest_name=reservation.guest_name,
        table_seats=reservation.seats_reserved,
        fired_at=order.fired_at,
        special_requests=order.special_requests,
        items=[
            BonItemLine(
                position=pos,
                quantity=item.quantity,
                item_name=item.item_name,
                unit_price=float(item.unit_price),
                subtotal=item.subtotal,
                notes=item.item_notes,
            )
            for pos, item in enumerate(filtered, start=1)
        ],
        subtotal_food=round(food_total, 2),
        subtotal_beverages=round(bev_total, 2),
        total_amount=float(order.total_amount),
    )


# ── Service class ─────────────────────────────────────────────────────────────

class OrderService:
    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_reservation(self, reservation_id: int) -> Reservation:
        r = self._db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if r is None:
            raise NotFoundException("Reservation", reservation_id)
        return r

    def _resolve_menu_items(self, requests: list) -> dict[int, MenuItem]:
        """
        Load all ordered menu items from the database in a single query
        and validate that they exist and are currently available.

        Raises:
            NotFoundException:  if any menu_item_id does not exist.
            ConflictException:  if any item is marked as unavailable.
        """
        ids   = [r.menu_item_id for r in requests]
        items = self._db.query(MenuItem).filter(MenuItem.id.in_(ids)).all()
        item_map = {i.id: i for i in items}

        missing = set(ids) - set(item_map.keys())
        if missing:
            raise NotFoundException("MenuItem", str(missing))

        unavailable = [item_map[i].name for i in ids if not item_map[i].is_available]
        if unavailable:
            raise ConflictException(
                f"The following items are currently unavailable: {', '.join(unavailable)}"
            )
        return item_map

    # ── Public API ────────────────────────────────────────────────────────────

    def create_or_update_order(
        self,
        reservation_id: int,
        payload:        CreateOrUpdateOrderRequest,
    ) -> OrderResponse:
        """
        Attach or replace a pre-order on a reservation.

        The order stays in PENDING_CHECKIN status – nothing is sent to the
        kitchen until the guest checks in.  Calling this endpoint multiple
        times replaces the previous order so guests can change their mind.

        Raises:
            NotFoundException:   if the reservation does not exist.
            ConflictException:   if the reservation is expired, cancelled, or
                                 the order has already been fired.
        """
        reservation = self._get_reservation(reservation_id)

        if reservation.status == ReservationStatus.EXPIRED:
            raise ConflictException("Reservation has expired – no order possible.")
        if reservation.status == ReservationStatus.CANCELLED:
            raise ConflictException("Reservation was cancelled – no order possible.")

        item_map = self._resolve_menu_items(payload.items)

        # Delete existing pre-order if present (guest is updating their order)
        existing = self._db.query(Order).filter(Order.reservation_id == reservation_id).first()
        if existing:
            if existing.status != OrderStatus.PENDING_CHECKIN:
                raise ConflictException(
                    f"Order cannot be modified once it has been fired (status: {existing.status})."
                )
            self._db.delete(existing)
            self._db.flush()

        # Build order items
        order_items = [
            OrderItem(
                menu_item_id=item_map[req.menu_item_id].id,
                quantity=req.quantity,
                unit_price=float(item_map[req.menu_item_id].price),
                item_name=item_map[req.menu_item_id].name,
                item_notes=req.item_notes,
            )
            for req in payload.items
        ]

        total = round(sum(float(i.unit_price) * i.quantity for i in order_items), 2)

        order = Order(
            reservation_id=reservation_id,
            status=OrderStatus.PENDING_CHECKIN,
            total_amount=total,
            special_requests=payload.special_requests,
            items=order_items,
        )
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)

        logger.info(
            "Pre-order saved for reservation %d: %d item(s), total=€%.2f",
            reservation_id, len(order_items), total,
        )
        return _order_to_response(order)

    def fire_order_on_checkin(self, reservation_id: int) -> FireOrderResponse:
        """
        Fire the pre-order when the guest checks in.

        Transitions the order from PENDING_CHECKIN to FIRED and generates
        a kitchen receipt (food items) and a bar receipt (beverages).
        If no pre-order exists, returns a success message with no receipts.

        Raises:
            NotFoundException: if the reservation does not exist.
        """
        reservation = self._get_reservation(reservation_id)
        order = self._db.query(Order).filter(Order.reservation_id == reservation_id).first()

        if order is None:
            # Guest arrived without a pre-order – that is fine
            return FireOrderResponse(
                message="Guest checked in – no pre-order on file.",
                order=None,
                kitchen_bon=None,
                bar_bon=None,
            )

        if order.status != OrderStatus.PENDING_CHECKIN:
            # Already fired (e.g. duplicate check-in call) – return existing data
            return FireOrderResponse(
                message=f"Order is already in status '{order.status}'. No changes made.",
                order=_order_to_response(order),
                kitchen_bon=None,
                bar_bon=None,
            )

        # Fire the order
        order.status   = OrderStatus.FIRED
        order.fired_at = datetime.now(tz=timezone.utc)
        self._db.commit()
        self._db.refresh(order)

        # Generate separate receipts for kitchen and bar
        kitchen_bon = _build_receipt(order, reservation, MenuItemType.FOOD,     "K", "KITCHEN")
        bar_bon     = _build_receipt(order, reservation, MenuItemType.BEVERAGE, "B", "BAR")

        logger.info(
            "Order %d FIRED for reservation %d | kitchen=%s | bar=%s",
            order.id, reservation_id,
            kitchen_bon.bon_number if kitchen_bon else "–",
            bar_bon.bon_number     if bar_bon     else "–",
        )

        return FireOrderResponse(
            message="Order fired! Receipts sent to kitchen and bar.",
            order=_order_to_response(order),
            kitchen_bon=kitchen_bon,
            bar_bon=bar_bon,
        )

    def get_order_by_reservation(self, reservation_id: int) -> OrderResponse:
        """
        Return the pre-order for a given reservation.

        Raises:
            NotFoundException: if no order exists for that reservation.
        """
        order = self._db.query(Order).filter(Order.reservation_id == reservation_id).first()
        if order is None:
            raise NotFoundException("Order for reservation", reservation_id)
        return _order_to_response(order)

    def update_order_status(self, order_id: int, new_status: OrderStatus) -> OrderResponse:
        """
        Advance an order through the kitchen workflow.

        Valid transitions:
            FIRED           → IN_PREPARATION, CANCELLED
            IN_PREPARATION  → READY,          CANCELLED
            READY           → SERVED

        Raises:
            NotFoundException:  if the order does not exist.
            ConflictException:  if the requested transition is not allowed.
        """
        order = self._db.query(Order).filter(Order.id == order_id).first()
        if order is None:
            raise NotFoundException("Order", order_id)

        valid_transitions: dict[OrderStatus, set[OrderStatus]] = {
            OrderStatus.FIRED:          {OrderStatus.IN_PREPARATION, OrderStatus.CANCELLED},
            OrderStatus.IN_PREPARATION: {OrderStatus.READY,          OrderStatus.CANCELLED},
            OrderStatus.READY:          {OrderStatus.SERVED},
        }
        allowed = valid_transitions.get(order.status, set())
        if new_status not in allowed:
            raise ConflictException(
                f"Transition from '{order.status}' to '{new_status}' is not allowed. "
                f"Allowed next statuses: {[s.value for s in allowed]}"
            )

        order.status = new_status
        self._db.commit()
        self._db.refresh(order)
        logger.info("Order id=%d status → %s", order_id, new_status.value)
        return _order_to_response(order)

    def list_active_orders(self) -> list[OrderResponse]:
        """
        Return all orders currently visible on the kitchen display.

        Includes orders in FIRED, IN_PREPARATION, and READY status,
        sorted oldest-first so the kitchen works through them in order.
        """
        orders = (
            self._db.query(Order)
            .filter(Order.status.in_([
                OrderStatus.FIRED,
                OrderStatus.IN_PREPARATION,
                OrderStatus.READY,
            ]))
            .order_by(Order.fired_at.asc())
            .all()
        )
        return [_order_to_response(o) for o in orders]