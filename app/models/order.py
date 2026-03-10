"""
Order and OrderItem ORM models.

An Order belongs to exactly one Reservation (one-to-one).
Guests create it as a pre-order before arriving; it stays in
PENDING_CHECKIN status until the guest checks in, at which point
it is FIRED and separate receipts are printed for the kitchen and bar.

Kitchen workflow after firing:
    FIRED ──► IN_PREPARATION ──► READY ──► SERVED
    Any non-terminal status ──► CANCELLED
"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrderStatus(str, Enum):
    PENDING_CHECKIN = "pending_checkin"  # stored, not yet sent to kitchen
    FIRED           = "fired"            # guest checked in – receipt printed
    IN_PREPARATION  = "in_preparation"   # kitchen is preparing the order
    READY           = "ready"            # order is ready to be served
    SERVED          = "served"           # guest has received the order
    CANCELLED       = "cancelled"        # order was cancelled


class Order(Base):
    __tablename__ = "orders"

    id:             Mapped[int]         = mapped_column(Integer, primary_key=True, index=True)
    reservation_id: Mapped[int]         = mapped_column(Integer, ForeignKey("reservations.id"), nullable=False, unique=True, index=True)
    status:         Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="orderstatus"),
        default=OrderStatus.PENDING_CHECKIN,
        nullable=False,
        index=True,
    )
    total_amount:     Mapped[float]       = mapped_column(Numeric(8, 2), nullable=False, default=0.0)
    special_requests: Mapped[str|None]    = mapped_column(Text, nullable=True)
    fired_at:         Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:       Mapped[datetime]    = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at:       Mapped[datetime]    = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    reservation: Mapped["Reservation"]   = relationship("Reservation", back_populates="order")  # noqa: F821
    items:       Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order id={self.id} reservation_id={self.reservation_id} status={self.status}>"


class OrderItem(Base):
    """A single line on an order (one menu item × quantity)."""

    __tablename__ = "order_items"

    id:           Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    order_id:     Mapped[int]      = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    menu_item_id: Mapped[int]      = mapped_column(Integer, ForeignKey("menu_items.id"), nullable=False)
    quantity:     Mapped[int]      = mapped_column(Integer, nullable=False, default=1)
    unit_price:   Mapped[float]    = mapped_column(Numeric(6, 2), nullable=False)  # price at time of order
    item_name:    Mapped[str]      = mapped_column(String(128), nullable=False)     # snapshot of name
    item_notes:   Mapped[str|None] = mapped_column(String(256), nullable=True)      # e.g. "no onions"

    order:     Mapped["Order"]    = relationship("Order", back_populates="items")
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="order_items")  # noqa: F821

    @property
    def subtotal(self) -> float:
        """Line total rounded to 2 decimal places."""
        return round(self.quantity * float(self.unit_price), 2)

    def __repr__(self) -> str:
        return f"<OrderItem id={self.id} item={self.item_name!r} qty={self.quantity}>"