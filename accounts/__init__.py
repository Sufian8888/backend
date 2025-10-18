"""
Accounts app initialization.
This file makes the permissions and other utilities available at the package level.
"""

from .permissions import (
    BaseRolePermission,
    IsAdmin,
    IsPurchasing,
    IsSales,
    role_required
)

from .role_permissions import (
    has_permission,
    ROLE_PERMISSIONS
)

__all__ = [
    'BaseRolePermission',
    'IsAdmin',
    'IsPurchasing',
    'IsSales',
    'role_required',
    'has_permission',
    'ROLE_PERMISSIONS'
]