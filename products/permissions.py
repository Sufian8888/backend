# app_name/permissions.py
from rest_framework.permissions import BasePermission

class IsAdminOrPurchasing(BasePermission):
    """
    Custom permission that allows access to users with role 'admin' or 'purchasing'.
    """

    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated and 
            (getattr(user, 'role', None) in ['admin', 'purchasing'] or user.is_staff)
        )
