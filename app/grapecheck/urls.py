from django.urls import path
from django.conf import settings
from django.utils.decorators import method_decorator
from . import views

# 常にBasic認証デコレータを適用（デコレータ内で環境変数をチェック）
from core.decorators import basic_auth_required

def conditional_auth_decorator(view_class):
    return method_decorator(basic_auth_required, name='dispatch')(view_class)

app_name = 'grapecheck'

urlpatterns = [
    # メインフォーム
    path('', conditional_auth_decorator(views.GrapeCheckFormView).as_view(), name='form'),
    
    # 結果表示
    path('results/<int:pk>/', conditional_auth_decorator(views.GrapeCheckResultView).as_view(), name='results'),
    
    # 履歴一覧
    path('history/', conditional_auth_decorator(views.GrapeCheckHistoryListView).as_view(), name='history'),
] 