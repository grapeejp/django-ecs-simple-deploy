from django.urls import path
from . import views

app_name = 'proofreading_ai'

urlpatterns = [
    path('', views.index, name='index'),
    path('proofread/', views.proofread, name='proofread'),
    path('history/', views.history, name='history'),
    path('dictionary/', views.dictionary, name='dictionary'),
] 