from rest_framework.routers import DefaultRouter

from orders.views import PurchaseOrderViewSet
from .views import SupplierViewSet

router = DefaultRouter()
router.register(r"suppliers", SupplierViewSet, basename="supplier")
router.register(r'purchase-orders', PurchaseOrderViewSet, basename="purchase-orders")


urlpatterns = router.urls
