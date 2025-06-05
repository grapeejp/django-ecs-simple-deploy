from django.urls import path
from . import views
from core.decorators import admin_login_required

app_name = 'grapecheck'

urlpatterns = [
    # メインフォーム
    path('', admin_login_required(views.GrapeCheckFormView.as_view()), name='form'),
    
    # 結果表示
    path('results/<int:pk>/', admin_login_required(views.GrapeCheckResultView.as_view()), name='results'),
    
    # 履歴一覧
    path('history/', admin_login_required(views.GrapeCheckHistoryListView.as_view()), name='history'),
] 