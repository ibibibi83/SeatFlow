"""
MenuItem ORM model.

Represents a single item on the Blockbräu Hamburg menu.
Items are grouped by category and split into FOOD and BEVERAGE types.
When is_available is set to False the item is hidden from the public
menu endpoint but still visible to management.
"""

from enum import Enum

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MenuCategory(str, Enum):
    # Food categories
    BREAD_PRETZEL = "Brezel & Brot"
    SOUP          = "Feine Suppen"
    STARTER       = "Vorspeisen & Gutes zum Bier"
    SALAD         = "Salate"
    FISH          = "Altonaer Fischmarkt"
    MAIN          = "Brauhausküche"
    GRILL         = "Vom Lavasteingrill"
    VEGETARIAN    = "Grüne Küche"
    SIDE          = "Beilagen"
    DESSERT       = "Dessert"
    # Beverage categories
    BEER_DRAFT        = "Hausgebraute Biere vom Fass"
    BEER_BOTTLE       = "Flaschenbiere"
    BEER_NONALCOHOLIC = "Alkoholfreies Bier"
    SOFT_DRINK        = "Softs & Säfte"
    HOT_DRINK         = "Heißgetränke"
    WINE              = "Wein & Perlendes"
    SPIRITS           = "Brände & Spirits"


class MenuItemType(str, Enum):
    FOOD     = "food"      # sent to the kitchen printer
    BEVERAGE = "beverage"  # sent to the bar printer


class MenuItem(Base):
    __tablename__ = "menu_items"

    id:           Mapped[int]          = mapped_column(Integer, primary_key=True, index=True)
    name:         Mapped[str]          = mapped_column(String(128), nullable=False)
    description:  Mapped[str|None]     = mapped_column(Text, nullable=True)
    category:     Mapped[MenuCategory] = mapped_column(SAEnum(MenuCategory, name="menucategory"), nullable=False, index=True)
    item_type:    Mapped[MenuItemType] = mapped_column(SAEnum(MenuItemType, name="menuitemtype"), nullable=False, index=True)
    price:        Mapped[float]        = mapped_column(Numeric(6, 2), nullable=False)
    unit:         Mapped[str|None]     = mapped_column(String(32),  nullable=True)   # e.g. "0.5 l", "300 g"
    allergens:    Mapped[str|None]     = mapped_column(String(256), nullable=True)
    is_available: Mapped[bool]         = mapped_column(Boolean, default=True, nullable=False)
    sort_order:   Mapped[int]          = mapped_column(Integer, default=0, nullable=False)

    order_items: Mapped[list["OrderItem"]] = relationship(  # noqa: F821
        "OrderItem", back_populates="menu_item"
    )

    def __repr__(self) -> str:
        return f"<MenuItem id={self.id} name={self.name!r} price={self.price}>"