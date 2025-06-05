from django.urls import path
from . import views
from core.decorators import admin_login_required

app_name = 'proofreading_ai'

urlpatterns = [
    path('', admin_login_required(views.index), name='index'),
    path('proofread/', admin_login_required(views.proofread), name='proofread'),
    path('proofread-async/', admin_login_required(views.proofread_async), name='proofread_async'),
    path('proofread-status/', admin_login_required(views.check_proofread_status), name='proofread_status'),
    path('history/', admin_login_required(views.history), name='history'),
    path('dictionary/', admin_login_required(views.dictionary), name='dictionary'),
    path('dictionary/add/', admin_login_required(views.add_dictionary), name='add_dictionary'),
    path('dictionary/viewer/', admin_login_required(views.dictionary_viewer), name='dictionary_viewer'),
    
    # フィードバック機能
    path('feedback/', admin_login_required(views.feedback_form), name='feedback_form'),
    path('feedback/submit/', admin_login_required(views.submit_feedback), name='submit_feedback'),
    
    # デバッグエンドポイント
    path('debug/aws-auth/', admin_login_required(views.debug_aws_auth), name='debug_aws_auth'),
    path('debug/server-status/', admin_login_required(views.debug_server_status), name='debug_server_status'),
] 