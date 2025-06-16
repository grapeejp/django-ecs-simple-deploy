from django.urls import path
from django.utils.decorators import method_decorator
from .views import DashboardView, create_users_debug, custom_logout, check_auth_status
from .decorators import basic_auth_required

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('debug/create-users/', create_users_debug, name='create_users_debug'),
    path('logout/', custom_logout, name='custom_logout'),
    path('api/auth-status/', check_auth_status, name='check_auth_status'),
] 