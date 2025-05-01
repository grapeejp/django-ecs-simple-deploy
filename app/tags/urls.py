from django.urls import path
from . import views

app_name = 'tags'

urlpatterns = [
    path('', views.tag_list, name='list'),
] 