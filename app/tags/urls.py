from django.urls import path
from django.conf import settings
from . import views

# 常にBasic認証デコレータを適用（デコレータ内で環境変数をチェック）
from core.decorators import basic_auth_required
auth_decorator = basic_auth_required

app_name = 'tags'

urlpatterns = [
    path('', auth_decorator(views.tag_list), name='list'),  # 関数を直接指定
] 