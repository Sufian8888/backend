from django.urls import path
from . import views
from . import import_views
urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('featured/', views.FeaturedProductsView.as_view(), name='featured_products'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('search-suggestions/', views.product_search_suggestions, name='search_suggestions'),
    path('filters/', views.product_filters, name='product_filters'),
        # Excel import endpoints
    path('import/excel/', import_views.import_products_excel, name='import_excel'),        # Full import with images
    path('import/fast/', import_views.import_products_fast, name='import_fast'),           # Fast bulk import
    path('import/test/', import_views.quick_import_test, name='quick_import_test'),        # Test endpoint  
    path('import/preview/', import_views.import_preview, name='import_preview'),
    path('site-settings/', views.site_settings, name='site_settings'),

    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'), 
    path('<int:id>/', views.ProductDetailView.as_view(), name='product_detail'),

]