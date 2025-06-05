from django.urls import path
from django.conf import settings
from .views import tag_list  # 明示的なインポート

# 環境に応じてBasic認証デコレータを適用
if getattr(settings, 'BASIC_AUTH_ENABLED', False):
    from core.decorators import basic_auth_required
    auth_decorator = basic_auth_required
else:
    # 認証デコレータを無効化（開発環境用）
    auth_decorator = lambda func: func

app_name = 'tags'

urlpatterns = [
    path('', auth_decorator(tag_list), name='list'),  # 関数を直接指定
] 