from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "manager"

# Add these new permission classes
class IsPurchasing(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["purchasing", "admin"]

class IsSales(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["sales", "admin"]

class IsAdminOrPurchasing(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["admin", "purchasing"]

class IsAdminOrSales(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["admin", "sales"]