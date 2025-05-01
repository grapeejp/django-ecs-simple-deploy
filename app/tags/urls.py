from django.urls import path
from .views import tag_list  # 明示的なインポート

app_name = 'tags'

urlpatterns = [
    path('', tag_list, name='list'),  # 関数を直接指定
] 