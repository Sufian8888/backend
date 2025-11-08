# filepath: backend/accounts/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.response import Response

class BaseRolePermission(BasePermission):
    role = None
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == self.role

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"

class IsPurchasing(BaseRolePermission):
    role = "purchasing"
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
            
        # Purchasing can only read (GET, HEAD, OPTIONS) by default
        if request.method in SAFE_METHODS:
            return True
            
        # Allow specific write operations
        safe_write_methods = getattr(view, 'purchasing_safe_methods', [])
        return request.method in safe_write_methods

class IsSales(BaseRolePermission):
    role = "sales"
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
            
        # Sales can read by default
        if request.method in SAFE_METHODS:
            return True
            
        # Allow specific write operations
        safe_write_methods = getattr(view, 'sales_safe_methods', [])
        return request.method in safe_write_methods

def role_required(roles):
    """
    Decorator for views that checks that the user has the required role.
    Usage: @role_required(['admin', 'purchasing'])
    """
    def decorator(view_func):
        def _wrapped_view(view, request, *args, **kwargs):
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required'}, 
                    status=403
                )
                
            if request.user.role not in roles:
                return Response(
                    {'error': 'You do not have permission to perform this action'}, 
                    status=403
                )
                
            return view_func(view, request, *args, **kwargs)
            
        return _wrapped_view
    return decorator