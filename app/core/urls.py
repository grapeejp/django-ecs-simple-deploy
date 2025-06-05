from django.urls import path
from .views import DashboardView
from .decorators import admin_login_required

urlpatterns = [
    path('', admin_login_required(DashboardView.as_view()), name='dashboard'),
] 