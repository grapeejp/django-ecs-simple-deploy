from django.urls import path
from . import views

app_name = 'tags'

urlpatterns = [
    # 後ほどこの部分に実際のパターンを追加する
    path('', views.tag_list, name='list'),
] 