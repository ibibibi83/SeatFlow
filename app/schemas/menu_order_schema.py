from datetime import datetime
from pydantic import BaseModel, Field


# ── MENÜ ──────────────────────────────────────────────────────────────────────

class MenuItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
    category: str
    item_type: str
    price: float
    unit: str | None
    allergens: str | None
    is_available: bool


class MenuCategoryGroup(BaseModel):
    category: str
    item_type: str
    items: list[MenuItemResponse]


class MenuResponse(BaseModel):
    food: list[MenuCategoryGroup]
    beverages: list[MenuCategoryGroup]


class UpdateMenuItemAvailabilityRequest(BaseModel):
    is_available: bool


# ── BESTELLUNG ────────────────────────────────────────────────────────────────

class OrderItemRequest(BaseModel):
    menu_item_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1, le=50)
    item_notes: str | None = Field(
        None, max_length=256,
        examples=["ohne Zwiebeln"]
    )


class CreateOrUpdateOrderRequest(BaseModel):
    items: list[OrderItemRequest] = Field(..., min_length=1)
    special_requests: str | None = Field(
        None, max_length=512,
        examples=["Glutenfreies Brot bitte"]
    )


class OrderItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    menu_item_id: int
    item_name: str
    quantity: int
    unit_price: float
    subtotal: float
    item_notes: str | None


class OrderResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    reservation_id: int
    status: str
    total_amount: float
    special_requests: str | None
    fired_at: datetime | None
    created_at: datetime
    items: list[OrderItemResponse]


# ── KÜCHEN- UND BAR-BON ───────────────────────────────────────────────────────

class BonItemLine(BaseModel):
    position: int
    quantity: int
    item_name: str
    unit_price: float
    subtotal: float
    notes: str | None


class KitchenBon(BaseModel):
    bon_number: str          # z.B. "BON-0042-K"
    bon_type: str            # "KÜCHE" oder "BAR"
    reservation_id: int
    confirmation_code: str
    guest_name: str
    table_seats: int
    fired_at: datetime
    special_requests: str | None
    items: list[BonItemLine]
    subtotal_food: float
    subtotal_beverages: float
    total_amount: float


class FireOrderResponse(BaseModel):
    message: str
    order: OrderResponse | None
    kitchen_bon: KitchenBon | None
    bar_bon: KitchenBon | None