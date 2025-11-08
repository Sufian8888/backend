from django.urls import path
from . import admin_views

app_name = 'admin_products'

urlpatterns = [
    # Dashboard stats
    path('stats/', admin_views.admin_dashboard_stats, name='dashboard_stats'),
    
    # Products CRUD
    path('products/', admin_views.AdminProductListCreateView.as_view(), name='product_list_create'),
    path('products/<int:pk>/', admin_views.AdminProductDetailView.as_view(), name='product_detail'),
    path('products/bulk-update/', admin_views.bulk_update_products, name='bulk_update_products'),
    
    # Categories CRUD
    path('categories/', admin_views.AdminCategoryListCreateView.as_view(), name='category_list_create'),
    path('categories/<int:pk>/', admin_views.AdminCategoryDetailView.as_view(), name='category_detail'),

    # System functions
    path('backup/', admin_views.create_database_backup, name='create_backup'),
    path('export-customers/', admin_views.export_customer_data, name='export_customers'),
    path('reports/', admin_views.reports_data, name='reports_data'),
    path('debug/', admin_views.debug_database_stats, name='debug_stats'),

    # Stock movements API
    path('stock-movements/', admin_views.StockMovementListCreateView.as_view(), name='stock_movements'),
]