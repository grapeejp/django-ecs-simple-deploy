from django.urls import path
from django.utils.decorators import method_decorator
from .views import DashboardView, create_users_debug
from .decorators import basic_auth_required

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('debug/create-users/', create_users_debug, name='create_users_debug'),
] 