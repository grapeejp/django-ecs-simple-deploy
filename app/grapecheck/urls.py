from django.urls import path
from . import views

app_name = 'grapecheck'

urlpatterns = [
    # メインフォーム
    path('', views.GrapeCheckFormView.as_view(), name='form'),
    
    # 結果表示
    path('results/<int:pk>/', views.GrapeCheckResultView.as_view(), name='results'),
    
    # 履歴一覧
    path('history/', views.GrapeCheckHistoryListView.as_view(), name='history'),
] 