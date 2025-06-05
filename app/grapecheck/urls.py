from django.urls import path
from django.conf import settings
from django.utils.decorators import method_decorator
from . import views

# 環境に応じてBasic認証デコレータを適用
if getattr(settings, 'BASIC_AUTH_ENABLED', False):
    from core.decorators import basic_auth_required
    # クラスベースビュー用のデコレータ
    def auth_class_decorator(view_class):
        return method_decorator(basic_auth_required, name='dispatch')(view_class)
else:
    # 認証デコレータを無効化（開発環境用）
    def auth_class_decorator(view_class):
        return view_class

app_name = 'grapecheck'

urlpatterns = [
    # メインフォーム
    path('', auth_class_decorator(views.GrapeCheckFormView).as_view(), name='form'),
    
    # 結果表示
    path('results/<int:pk>/', auth_class_decorator(views.GrapeCheckResultView).as_view(), name='results'),
    
    # 履歴一覧
    path('history/', auth_class_decorator(views.GrapeCheckHistoryListView).as_view(), name='history'),
] 