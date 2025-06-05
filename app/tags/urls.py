from django.urls import path
from .views import tag_list  # 明示的なインポート
from core.decorators import admin_login_required

app_name = 'tags'

urlpatterns = [
    path('', admin_login_required(tag_list), name='list'),  # 関数を直接指定
] 