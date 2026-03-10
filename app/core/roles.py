"""
User role definitions and permission groups.

Roles follow a simple hierarchy:
  guest              – walk-in guests, no login required for most actions
  shift_manager      – can view reservations and manage orders
  operations_manager – full access including quota management and user creation
"""

from enum import Enum


class UserRole(str, Enum):
    GUEST              = "guest"
    SHIFT_MANAGER      = "shift_manager"
    OPERATIONS_MANAGER = "operations_manager"


# Roles that have access to management endpoints
MANAGEMENT_ROLES = frozenset({UserRole.SHIFT_MANAGER, UserRole.OPERATIONS_MANAGER})

# Roles that can change the seat quota
QUOTA_ROLES = frozenset({UserRole.OPERATIONS_MANAGER})