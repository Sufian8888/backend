from django.urls import path
from . import views

urlpatterns = [
    path('', views.FavoriteListView.as_view(), name='favorites'),
    path('add/', views.add_to_favorites, name='add_to_favorites'),
    path('remove/<int:product_id>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('check/<int:product_id>/', views.check_favorite, name='check_favorite'),
    path('clear/', views.clear_favorites, name='clear_favorites'),
    path('toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
]
