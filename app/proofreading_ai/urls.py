from django.urls import path
from . import views

app_name = 'proofreading_ai'

urlpatterns = [
    path('', views.index, name='index'),
    path('proofread/', views.proofread, name='proofread'),
    path('proofread-async/', views.proofread_async, name='proofread_async'),
    path('proofread-status/', views.check_proofread_status, name='proofread_status'),
    path('history/', views.history, name='history'),
    path('dictionary/', views.dictionary, name='dictionary'),
    path('dictionary/add/', views.add_dictionary, name='add_dictionary'),
] 