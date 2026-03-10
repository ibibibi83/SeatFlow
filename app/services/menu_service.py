"""
Menu service.

Retrieves and groups menu items for public and management endpoints.
Availability toggling (e.g. "sold out") is also handled here.
"""

import logging
from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.menu_item import MenuItem, MenuItemType
from app.schemas.menu_order_schema import (
    MenuCategoryGroup,
    MenuItemResponse,
    MenuResponse,
)

logger = logging.getLogger(__name__)


class MenuService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_full_menu(self) -> MenuResponse:
        """
        Return the public menu: available items only, grouped by category.

        Food and beverages are returned as separate lists so the frontend
        can render them in different sections without additional filtering.
        """
        items = (
            self._db.query(MenuItem)
            .filter(MenuItem.is_available == True)  # noqa: E712
            .order_by(MenuItem.category, MenuItem.sort_order, MenuItem.name)
            .all()
        )

        food_map: dict[str, list[MenuItemResponse]] = defaultdict(list)
        bev_map:  dict[str, list[MenuItemResponse]] = defaultdict(list)

        for item in items:
            resp = MenuItemResponse.model_validate(item)
            if item.item_type == MenuItemType.FOOD:
                food_map[item.category.value].append(resp)
            else:
                bev_map[item.category.value].append(resp)

        food_groups = [MenuCategoryGroup(category=cat, item_type="food",     items=its) for cat, its in food_map.items()]
        bev_groups  = [MenuCategoryGroup(category=cat, item_type="beverage", items=its) for cat, its in bev_map.items()]

        return MenuResponse(food=food_groups, beverages=bev_groups)

    def list_all_items(self) -> list[MenuItemResponse]:
        """
        Return every menu item including unavailable ones.
        Intended for management use – staff can see what is marked as sold out.
        """
        items = (
            self._db.query(MenuItem)
            .order_by(MenuItem.category, MenuItem.sort_order)
            .all()
        )
        return [MenuItemResponse.model_validate(i) for i in items]

    def get_item_by_id(self, item_id: int) -> MenuItem:
        """
        Fetch a single MenuItem by primary key.

        Raises:
            NotFoundException: if no item with that id exists.
        """
        item = self._db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if item is None:
            raise NotFoundException("MenuItem", item_id)
        return item

    def set_availability(self, item_id: int, is_available: bool) -> MenuItemResponse:
        """
        Toggle whether an item appears on the public menu.

        Useful for marking dishes as sold out mid-service without
        deleting them from the database.

        Raises:
            NotFoundException: if no item with that id exists.
        """
        item = self.get_item_by_id(item_id)
        item.is_available = is_available
        self._db.commit()
        self._db.refresh(item)
        logger.info("MenuItem id=%d availability set to %s.", item_id, is_available)
        return MenuItemResponse.model_validate(item)