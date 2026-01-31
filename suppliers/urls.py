from rest_framework.routers import DefaultRouter

from .views import SupplierViewSet

router = DefaultRouter()
router.register(r"suppliers", SupplierViewSet, basename="supplier")
# purchase-orders handled by purchases app only (orders.PurchaseOrder was wrong table)

urlpatterns = router.urls
