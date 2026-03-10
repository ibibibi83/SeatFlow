"""
Menu routes.

GET   /menu             – full public menu (available items only)
GET   /menu/all         – all items including unavailable (management)
PATCH /menu/{id}/availability – toggle item availability (management)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import ManagementUser
from app.db.session import get_db
from app.schemas.menu_order_schema import (
    MenuItemResponse,
    MenuResponse,
    UpdateMenuItemAvailabilityRequest,
)
from app.services.menu_service import MenuService

router = APIRouter(prefix="/menu", tags=["Menu"])


def _get_menu_service(db: Annotated[Session, Depends(get_db)]) -> MenuService:
    return MenuService(db)


MenuServiceDep = Annotated[MenuService, Depends(_get_menu_service)]


@router.get(
    "",
    response_model=MenuResponse,
    status_code=status.HTTP_200_OK,
    summary="Full Blockbräu menu grouped by category (public)",
)
def get_menu(service: MenuServiceDep) -> MenuResponse:
    """
    Returns all available dishes and drinks, grouped by category.
    No login required – guests can browse the menu before reserving.
    """
    return service.get_full_menu()


@router.get(
    "/all",
    response_model=list[MenuItemResponse],
    summary="All menu items including unavailable (management only)",
)
def list_all_items(
    service: MenuServiceDep,
    _:       ManagementUser,
) -> list[MenuItemResponse]:
    """
    Shows every item regardless of availability.
    Useful for staff to see what is currently marked as sold out.
    """
    return service.list_all_items()


@router.patch(
    "/{item_id}/availability",
    response_model=MenuItemResponse,
    summary="Mark a menu item as available or unavailable (management only)",
)
def set_availability(
    item_id: int,
    payload: UpdateMenuItemAvailabilityRequest,
    service: MenuServiceDep,
    _:       ManagementUser,
) -> MenuItemResponse:
    """
    Toggle item visibility on the public menu.
    For example: set is_available=false when a dish is sold out.
    The item reappears on the public menu as soon as is_available is set back to true.
    """
    return service.set_availability(item_id, payload.is_available)