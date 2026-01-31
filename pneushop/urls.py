"""pneushop URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/auth/', include('accounts.urls')),
    path('api/accounts/', include('accounts.urls')),  # Single include for all account URLs

    path('api/products/', include('products.urls')),
    path('api/admin/', include('products.admin_urls')),
    path('api/cart/', include('cart.urls')),
    path('api/favorites/', include('favorites.urls')),
    path('api/', include('accounts.urls')),
    
    # IMPORTANT: purchases MUST come before orders to avoid routing conflicts
    path("api/", include("suppliers.urls")),
    path("api/", include("purchases.urls")),  # ← Purchases FIRST (buying FROM suppliers)
    
    path('api/orders/', include('orders.urls')),
    path("api/", include("orders.urls")),      # ← Orders SECOND (selling TO clients)

    path('test-email/', views.index, name='test-email'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
