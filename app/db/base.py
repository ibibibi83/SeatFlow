"""
SQLAlchemy declarative base.

All ORM models must inherit from this Base so that
Base.metadata.create_all() can discover and create their tables.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so SQLAlchemy can discover them
# when Base.metadata.create_all() is called.
from app.models.user import User  # noqa: F401, E402
from app.models.reservation import Reservation  # noqa: F401, E402
from app.models.menu_item import MenuItem  # noqa: F401, E402
from app.models.order import Order  # noqa: F401, E402
from app.models.seat_quota import SeatQuota  # noqa: F401, E402