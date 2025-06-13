from django.urls import path
from django.utils.decorators import method_decorator
from .views import DashboardView, create_users_debug, health_check, debug_env, dashboard_data
from .decorators import basic_auth_required

app_name = 'core'

urlpatterns = [
    path('dashboard/', basic_auth_required(DashboardView.as_view()), name='dashboard'),
    path('api/dashboard-data/', basic_auth_required(dashboard_data), name='dashboard_data'),
    path('debug/create-users/', create_users_debug, name='create_users_debug'),
    path('health/', health_check, name='health_check'),
    path('debug/env/', debug_env, name='debug_env'),
]