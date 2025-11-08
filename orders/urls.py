from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeliveryViewSet, OrderListCreateView, OrderDetailView, PurchaseOrderViewSet
router = DefaultRouter()
router.register(r'purchase-orders', PurchaseOrderViewSet, basename="purchase-orders")
router.register(r'deliveries', DeliveryViewSet, basename='delivery')
urlpatterns = [
    path('', OrderListCreateView.as_view(), name='orders-list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('', include(router.urls)),   # 👈 include router-generated URLs
    path('api/', include(router.urls)),
]
