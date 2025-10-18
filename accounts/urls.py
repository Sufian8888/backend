# from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView
# from . import views

# urlpatterns = [
#     path('register/', views.RegisterView.as_view(), name='register'),
#     path('login/', views.login_view, name='login'),
#     path('verify-email/', views.verify_email, name='verify_email'),
#     path('forgot-password/', views.forgot_password, name='forgot_password'),
#     path('verify-reset-token/', views.verify_reset_token, name='verify_reset_token'),
#     path('reset-password/', views.reset_password, name='reset_password'),
#     path('user/', views.user_profile, name='user_profile'),
#     path('clients/', views.clients_list, name='clients_list'),  # new endpoint
#     path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('create-user/', views.create_user, name='create_user'),
#     path('staff-users/', views.list_staff_users, name='list_staff_users'),  # List staff users
# ]

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .views import update_user, delete_user

urlpatterns = [
    # Authentication
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/verify-email/', views.verify_email, name='verify_email'),
    path('auth/forgot-password/', views.forgot_password, name='forgot_password'),
    path('auth/verify-reset-token/', views.verify_reset_token, name='verify_reset_token'),
    path('auth/reset-password/', views.reset_password, name='reset_password'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User management
    path('user/', views.user_profile, name='user_profile'),
    path('clients/', views.clients_list, name='clients_list'),
    
    # Admin endpoints
    path('admin/create-user/', views.create_user, name='create_user'),
    path('admin/staff-users/', views.list_staff_users, name='list_staff_users'),
    path('admin/update-user/<int:user_id>/', update_user, name='update-user'),
    path('admin/delete-user/<int:user_id>/', delete_user, name='delete-user'),

]