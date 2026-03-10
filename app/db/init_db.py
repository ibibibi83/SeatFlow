"""
Database initialisation: table creation and seed data.

Called once on application startup via the lifespan hook in main.py.
Safe to run multiple times – seed functions check for existing rows
before inserting so no data is duplicated on restart.
"""

import logging

from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine

logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Create all tables and populate seed data.

    Import order matters: every model must be imported before
    Base.metadata.create_all() is called so SQLAlchemy knows about it.
    """
    import app.models.menu_item    # noqa: F401
    import app.models.order        # noqa: F401
    import app.models.reservation  # noqa: F401
    import app.models.seat_quota   # noqa: F401
    import app.models.user         # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")

    db = SessionLocal()
    try:
        _seed_quota(db)
        _seed_users(db)
        _seed_menu(db)
    finally:
        db.close()


def _seed_quota(db: Session) -> None:
    from app.core.config import settings
    from app.models.seat_quota import SeatQuota

    if db.query(SeatQuota).first() is None:
        db.add(SeatQuota(
            total_seats=settings.TOTAL_SEATS,
            reservable_seats=settings.RESERVABLE_SEATS,
        ))
        db.commit()
        logger.info(
            "Default seat quota created: %d reservable out of %d total.",
            settings.RESERVABLE_SEATS, settings.TOTAL_SEATS,
        )


def _seed_users(db: Session) -> None:
    from app.core.roles import UserRole
    from app.core.security import hash_password
    from app.models.user import User

    default_users = [
        dict(
            username="ops_manager",
            email="ops@blockbraeu.local",
            full_name="Operations Manager",
            plain_pw="ops123",
            role=UserRole.OPERATIONS_MANAGER,
        ),
        dict(
            username="shift_manager",
            email="shift@blockbraeu.local",
            full_name="Shift Manager",
            plain_pw="shift123",
            role=UserRole.SHIFT_MANAGER,
        ),
    ]

    for u in default_users:
        if not db.query(User).filter(User.username == u["username"]).first():
            db.add(User(
                username=u["username"],
                email=u["email"],
                full_name=u["full_name"],
                hashed_password=hash_password(u["plain_pw"]),
                role=u["role"],
                is_active=True,
            ))
            logger.info("Default user created: %s (%s)", u["username"], u["role"])
    db.commit()


def _seed_menu(db: Session) -> None:
    from app.models.menu_item import MenuItem, MenuCategory, MenuItemType

    if db.query(MenuItem).count() > 0:
        logger.info("Menu already seeded – skipping.")
        return

    items = [
        dict(name="Laugenbrezel", description="Freshly baked soft pretzel served with butter.", category=MenuCategory.BREAD_PRETZEL, item_type=MenuItemType.FOOD, price=3.90, allergens="Gluten, Milk", sort_order=1),
        dict(name="Bread basket", description="House-made bread with butter and beer mustard.", category=MenuCategory.BREAD_PRETZEL, item_type=MenuItemType.FOOD, price=4.50, allergens="Gluten, Milk, Mustard", sort_order=2),
        dict(name="Pretzel with Obazda", description="Soft pretzel with Bavarian camembert spread and roasted onions.", category=MenuCategory.BREAD_PRETZEL, item_type=MenuItemType.FOOD, price=6.90, allergens="Gluten, Milk", sort_order=3),
        dict(name="Hamburg eel soup", description="Traditional Hamburg speciality with smoked eel and prunes.", category=MenuCategory.SOUP, item_type=MenuItemType.FOOD, price=9.90, allergens="Fish, Celery", sort_order=1),
        dict(name="Beef goulash soup", description="Hearty beef goulash soup with paprika, served with bread.", category=MenuCategory.SOUP, item_type=MenuItemType.FOOD, price=8.90, allergens="Gluten, Celery", sort_order=2),
        dict(name="Brewhouse platter", description="Cured ham, mini patties, pepper sausage with radish and beer mustard.", category=MenuCategory.STARTER, item_type=MenuItemType.FOOD, price=16.90, allergens="Gluten, Mustard, Celery", sort_order=1),
        dict(name="Beef tartar", description="100% beef, seasoned with onions, capers and horseradish.", category=MenuCategory.STARTER, item_type=MenuItemType.FOOD, price=17.90, allergens="Mustard, Egg, Celery", sort_order=2),
        dict(name="Obazda", description="Bavarian camembert cream cheese with roasted onions and pretzels.", category=MenuCategory.STARTER, item_type=MenuItemType.FOOD, price=9.90, allergens="Gluten, Milk", sort_order=3),
        dict(name="Brewhouse patties (3 pcs)", description="House-made beef patties served with beer mustard.", category=MenuCategory.STARTER, item_type=MenuItemType.FOOD, price=11.90, allergens="Gluten, Egg, Mustard", sort_order=4),
        dict(name="Fish patties (2 pcs)", description="Hand-made fish patties with radish and horseradish.", category=MenuCategory.FISH, item_type=MenuItemType.FOOD, price=16.90, allergens="Fish, Gluten, Egg, Mustard", sort_order=1),
        dict(name="Beer-battered fish", description="Crispy beer-battered fish with remoulade and potato salad.", category=MenuCategory.FISH, item_type=MenuItemType.FOOD, price=19.90, allergens="Fish, Gluten, Egg, Milk, Mustard", sort_order=2),
        dict(name="Hamburg pan fish", description="Pan-fried coalfish with fried potatoes and mustard sauce.", category=MenuCategory.FISH, item_type=MenuItemType.FOOD, price=22.90, allergens="Fish, Gluten, Milk, Mustard", sort_order=3),
        dict(name="Pork knuckle (approx. 700 g)", description="Crispy oven-roasted pork knuckle with sauerkraut and beer mustard.", category=MenuCategory.MAIN, item_type=MenuItemType.FOOD, price=24.90, unit="approx. 700 g", allergens="Gluten, Mustard", sort_order=1),
        dict(name="Veal Wiener Schnitzel", description="Authentic breaded veal schnitzel with fries and cranberries.", category=MenuCategory.MAIN, item_type=MenuItemType.FOOD, price=26.90, allergens="Gluten, Egg, Milk", sort_order=2),
        dict(name="Pork schnitzel", description="Breaded pork schnitzel with fries and salad.", category=MenuCategory.MAIN, item_type=MenuItemType.FOOD, price=19.90, allergens="Gluten, Egg, Milk", sort_order=3),
        dict(name="Brewhouse goulash", description="Slow-cooked beef with fresh peppers and mashed potatoes.", category=MenuCategory.MAIN, item_type=MenuItemType.FOOD, price=21.90, allergens="Gluten, Celery", sort_order=4),
        dict(name="Bratwurst (2 pcs)", description="House-made coarse bratwurst with sauerkraut and beer mustard.", category=MenuCategory.MAIN, item_type=MenuItemType.FOOD, price=17.90, allergens="Gluten, Mustard", sort_order=5),
        dict(name="Half roast chicken", description="Grilled half chicken with fried potatoes and salad.", category=MenuCategory.MAIN, item_type=MenuItemType.FOOD, price=18.90, allergens="Mustard", sort_order=6),
        dict(name="Rump steak (300 g)", description="BLOCK HOUSE rump steak from the lava stone grill, with fries and salad.", category=MenuCategory.GRILL, item_type=MenuItemType.FOOD, price=34.90, unit="300 g", allergens="Mustard", sort_order=1),
        dict(name="Entrecôte (300 g)", description="BLOCK HOUSE entrecôte from the lava stone grill, with fries and salad.", category=MenuCategory.GRILL, item_type=MenuItemType.FOOD, price=36.90, unit="300 g", allergens="Mustard", sort_order=2),
        dict(name="Vegan brewhouse burger", description="Veggie patty, lettuce, tomato, house sauce and fries.", category=MenuCategory.VEGETARIAN, item_type=MenuItemType.FOOD, price=16.90, allergens="Gluten, Sesame, Mustard", sort_order=1),
        dict(name="Seasonal vegetable curry", description="Seasonal vegetables in curry sauce with basmati rice and naan.", category=MenuCategory.VEGETARIAN, item_type=MenuItemType.FOOD, price=15.90, allergens="Gluten, Milk", sort_order=2),
        dict(name="French fries", description="Served with ketchup or mayonnaise.", category=MenuCategory.SIDE, item_type=MenuItemType.FOOD, price=4.90, allergens="Egg (mayo)", sort_order=1),
        dict(name="Fried potatoes", description="Pan-fried with bacon and roasted onions.", category=MenuCategory.SIDE, item_type=MenuItemType.FOOD, price=5.90, sort_order=2),
        dict(name="Sauerkraut", description="Dithmarschen sauerkraut braised with bay leaf.", category=MenuCategory.SIDE, item_type=MenuItemType.FOOD, price=4.90, sort_order=3),
        dict(name="Baguette", description="Fresh baguette with butter.", category=MenuCategory.SIDE, item_type=MenuItemType.FOOD, price=3.50, allergens="Gluten, Milk", sort_order=4),
        dict(name="Red berry compote", description="House-made red berry compote with vanilla sauce.", category=MenuCategory.DESSERT, item_type=MenuItemType.FOOD, price=7.50, allergens="Milk", sort_order=1),
        dict(name="Apple strudel", description="Warm apple strudel with vanilla sauce and cinnamon.", category=MenuCategory.DESSERT, item_type=MenuItemType.FOOD, price=8.50, allergens="Gluten, Milk, Egg", sort_order=2),
        dict(name="Cheesecake", description="Classic North German cheesecake.", category=MenuCategory.DESSERT, item_type=MenuItemType.FOOD, price=7.90, allergens="Gluten, Milk, Egg", sort_order=3),
        dict(name="BLOCKBRÄU Lager (0.3 l)", description="Unfiltered harbour lager, freshly tapped.", category=MenuCategory.BEER_DRAFT, item_type=MenuItemType.BEVERAGE, price=4.80, unit="0.3 l", allergens="Gluten", sort_order=1),
        dict(name="BLOCKBRÄU Lager (0.5 l)", description="Unfiltered harbour lager, freshly tapped.", category=MenuCategory.BEER_DRAFT, item_type=MenuItemType.BEVERAGE, price=6.50, unit="0.5 l", allergens="Gluten", sort_order=2),
        dict(name="BLOCKBRÄU Lager (1.0 l)", description="The big stein.", category=MenuCategory.BEER_DRAFT, item_type=MenuItemType.BEVERAGE, price=12.50, unit="1.0 l", allergens="Gluten", sort_order=3),
        dict(name="BLOCKBRÄU Wheat beer (0.5 l)", description="Unfiltered hefeweizen – fruity and spiced.", category=MenuCategory.BEER_DRAFT, item_type=MenuItemType.BEVERAGE, price=6.50, unit="0.5 l", allergens="Gluten, Wheat", sort_order=4),
        dict(name="Seasonal special (0.5 l)", description="The head brewer's current speciality.", category=MenuCategory.BEER_DRAFT, item_type=MenuItemType.BEVERAGE, price=6.90, unit="0.5 l", allergens="Gluten", sort_order=5),
        dict(name="BLOCKBRÄU Alcohol-free (0.33 l)", description="House-brewed alcohol-free beer.", category=MenuCategory.BEER_NONALCOHOLIC, item_type=MenuItemType.BEVERAGE, price=4.50, unit="0.33 l", allergens="Gluten", sort_order=1),
        dict(name="BLOCKBRÄU Alcohol-free (0.5 l)", description="House-brewed alcohol-free beer.", category=MenuCategory.BEER_NONALCOHOLIC, item_type=MenuItemType.BEVERAGE, price=6.00, unit="0.5 l", allergens="Gluten", sort_order=2),
        dict(name="Coca-Cola (0.3 l)", category=MenuCategory.SOFT_DRINK, item_type=MenuItemType.BEVERAGE, price=3.90, unit="0.3 l", sort_order=1),
        dict(name="Coca-Cola (0.5 l)", category=MenuCategory.SOFT_DRINK, item_type=MenuItemType.BEVERAGE, price=5.20, unit="0.5 l", sort_order=2),
        dict(name="Fanta (0.3 l)", category=MenuCategory.SOFT_DRINK, item_type=MenuItemType.BEVERAGE, price=3.90, unit="0.3 l", sort_order=3),
        dict(name="Sprite (0.3 l)", category=MenuCategory.SOFT_DRINK, item_type=MenuItemType.BEVERAGE, price=3.90, unit="0.3 l", sort_order=4),
        dict(name="Sparkling water (0.25 l)", description="Still or sparkling.", category=MenuCategory.SOFT_DRINK, item_type=MenuItemType.BEVERAGE, price=3.20, unit="0.25 l", sort_order=5),
        dict(name="Sparkling water (0.75 l)", description="Still or sparkling.", category=MenuCategory.SOFT_DRINK, item_type=MenuItemType.BEVERAGE, price=7.50, unit="0.75 l", sort_order=6),
        dict(name="Apple spritzer (0.3 l)", description="Regional apple juice with sparkling water.", category=MenuCategory.SOFT_DRINK, item_type=MenuItemType.BEVERAGE, price=4.20, unit="0.3 l", sort_order=7),
        dict(name="Filter coffee", description="Freshly brewed filter coffee.", category=MenuCategory.HOT_DRINK, item_type=MenuItemType.BEVERAGE, price=3.50, unit="0.2 l", sort_order=1),
        dict(name="Cappuccino", description="Espresso with steamed milk foam.", category=MenuCategory.HOT_DRINK, item_type=MenuItemType.BEVERAGE, price=4.20, allergens="Milk", sort_order=2),
        dict(name="Latte macchiato", description="Espresso layered in steamed milk.", category=MenuCategory.HOT_DRINK, item_type=MenuItemType.BEVERAGE, price=4.50, allergens="Milk", sort_order=3),
        dict(name="Tea (pot)", description="Choice of tea varieties.", category=MenuCategory.HOT_DRINK, item_type=MenuItemType.BEVERAGE, price=4.50, unit="0.4 l", sort_order=4),
        dict(name="White wine (0.2 l)", description="House white wine, dry.", category=MenuCategory.WINE, item_type=MenuItemType.BEVERAGE, price=6.50, unit="0.2 l", allergens="Sulphites", sort_order=1),
        dict(name="Red wine (0.2 l)", description="House red wine, dry.", category=MenuCategory.WINE, item_type=MenuItemType.BEVERAGE, price=6.50, unit="0.2 l", allergens="Sulphites", sort_order=2),
        dict(name="Sparkling wine (0.1 l)", description="Brut, dry.", category=MenuCategory.WINE, item_type=MenuItemType.BEVERAGE, price=5.90, unit="0.1 l", allergens="Sulphites", sort_order=3),
        dict(name="Hamburg grain schnapps (4 cl)", description="Classic North German clear spirit.", category=MenuCategory.SPIRITS, item_type=MenuItemType.BEVERAGE, price=4.50, unit="4 cl", allergens="Gluten", sort_order=1),
        dict(name="Whisky (4 cl)", description="Johnnie Walker Red Label.", category=MenuCategory.SPIRITS, item_type=MenuItemType.BEVERAGE, price=7.50, unit="4 cl", allergens="Gluten", sort_order=2),
        dict(name="Gin (4 cl)", description="Tanqueray London Dry.", category=MenuCategory.SPIRITS, item_type=MenuItemType.BEVERAGE, price=7.90, unit="4 cl", sort_order=3),
        dict(name="Jägermeister (4 cl)", description="The classic herbal liqueur.", category=MenuCategory.SPIRITS, item_type=MenuItemType.BEVERAGE, price=5.50, unit="4 cl", sort_order=4),
    ]

    db.add_all([
        MenuItem(
            name=d["name"],
            description=d.get("description"),
            category=d["category"],
            item_type=d["item_type"],
            price=d["price"],
            unit=d.get("unit"),
            allergens=d.get("allergens"),
            is_available=True,
            sort_order=d.get("sort_order", 0),
        )
        for d in items
    ])
    db.commit()
    logger.info("Menu seeded: %d items.", len(items))