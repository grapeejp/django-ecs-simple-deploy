from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.cache import never_cache
import json
from django.utils import timezone

class DashboardView(LoginRequiredMixin, TemplateView):
    """ダッシュボード表示ビュー（ログイン必須）"""
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ここに必要なコンテキストデータを追加
        return context 

def dashboard_view(request):
    """ダッシュボード表示ビュー（ログイン必須）"""
    return render(request, 'dashboard/index.html')

@csrf_exempt
@require_http_methods(["POST"])
def create_users_debug(request):
    """デバッグ用ユーザー作成API"""
    try:
        data = json.loads(request.body)
        users_data = data.get('users', [])
        
        created_users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                }
            )
            if created:
                user.set_password(user_data.get('password', 'defaultpassword'))
                user.save()
            created_users.append({
                'username': user.username,
                'email': user.email,
                'created': created
            })
        
        return JsonResponse({
            'status': 'success',
            'users': created_users
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@never_cache
@csrf_protect
def custom_logout(request):
    """カスタムログアウトビュー - セッションとクッキーを強制的にクリア"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'ログアウトしました。')
        return redirect('account_login')
    
    return render(request, 'account/logout.html')

@never_cache  # キャッシュ完全無効化
@csrf_exempt  # API用
def check_auth_status(request):
    """認証状態をチェックするAPI（キャッシュ無効化対応）"""
    response_data = {
        'authenticated': request.user.is_authenticated,
        'user': None,
        'timestamp': timezone.now().isoformat()  # タイムスタンプ追加
    }
    
    if request.user.is_authenticated:
        # 許可されたユーザーかチェック
        allowed_emails = [
            'test@grapee.co.jp',
            'yanagimoto@grapee.co.jp',
            'yasutoshi.yanagimoto@grapee.co.jp',
        ]
        
        if request.user.email in allowed_emails:
            response_data['user'] = {
                'email': request.user.email,
                'username': request.user.username,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }
        else:
            response_data['authenticated'] = False
            response_data['error'] = 'Access denied: User not in allowed list'
    
    response = JsonResponse(response_data)
    
    # キャッシュ無効化ヘッダー
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response 