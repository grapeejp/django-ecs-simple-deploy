from django.urls import path
from django.conf import settings
from . import views

# 環境に応じてBasic認証デコレータを適用
if getattr(settings, 'BASIC_AUTH_ENABLED', False):
    from core.decorators import basic_auth_required
    auth_decorator = basic_auth_required
else:
    # 認証デコレータを無効化（開発環境用）
    auth_decorator = lambda func: func

app_name = 'proofreading_ai'

urlpatterns = [
    path('', auth_decorator(views.index), name='index'),
    path('proofread/', auth_decorator(views.proofread), name='proofread'),
    path('proofread-async/', auth_decorator(views.proofread_async), name='proofread_async'),
    path('proofread-status/', auth_decorator(views.check_proofread_status), name='proofread_status'),
    path('history/', auth_decorator(views.history), name='history'),
    path('dictionary/', auth_decorator(views.dictionary), name='dictionary'),
    path('dictionary/add/', auth_decorator(views.add_dictionary), name='add_dictionary'),
    path('dictionary/viewer/', auth_decorator(views.dictionary_viewer), name='dictionary_viewer'),
    
    # フィードバック機能
    path('feedback/', views.feedback_form, name='feedback_form'),
    path('feedback/submit/', views.submit_feedback, name='submit_feedback'),
    
    # デバッグエンドポイント
    path('debug/aws-auth/', auth_decorator(views.debug_aws_auth), name='debug_aws_auth'),
    path('debug/server-status/', auth_decorator(views.debug_server_status), name='debug_server_status'),
] 