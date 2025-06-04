from django.urls import path
from django.utils.decorators import method_decorator
from .views import DashboardView
from .decorators import basic_auth_required

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
] 