from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

class DashboardView(LoginRequiredMixin, TemplateView):
    """ダッシュボード表示ビュー（ログイン必須）"""
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ここに必要なコンテキストデータを追加
        return context 

def dashboard_view(request):
    """ダッシュボードのメインビュー"""
    # ユーザーがログインしていない場合はログインページに
    if not request.user.is_authenticated:
        return render(request, 'registration/login.html')
    
    context = {
        'user': request.user,
        'apps': [
            {
                'name': '文章校正AI',
                'description': 'AI技術で文章を自動校正',
                'url': '/proofreading_ai/',
                'icon': '📝'
            },
            {
                'name': 'タグ推薦システム',
                'description': 'コンテンツに最適なタグを提案',
                'url': '/tags/',
                'icon': '🏷️'
            },
            {
                'name': 'グレイプらしさチェッカー',
                'description': 'グレイプブランドの一貫性をチェック',
                'url': '/grapecheck/',
                'icon': '🍇'
            }
        ]
    }
    return render(request, 'dashboard/dashboard.html', context)

@csrf_exempt
def create_users_debug(request):
    """デバッグ用: ユーザー作成エンドポイント"""
    demo_users = [
        ('admin', 'admin@grapee.co.jp', 'grape2025admin', True, True),
        ('testuser', 'test@grapee.co.jp', 'grape2025test', True, False),
        ('demo1', 'demo1@grapee.co.jp', 'grape2025demo', False, False),
        ('demo2', 'demo2@grapee.co.jp', 'grape2025demo', False, False),
        ('demo3', 'demo3@grapee.co.jp', 'grape2025demo', False, False),
    ]
    
    results = []
    for username, email, password, is_staff, is_superuser in demo_users:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': is_staff,
                'is_superuser': is_superuser
            }
        )
        user.set_password(password)
        user.save()
        
        status = "作成" if created else "更新"
        results.append(f'{status}: {username} ({email})')
    
    # ユーザー一覧も追加
    all_users = []
    for u in User.objects.all():
        all_users.append({
            'username': u.username,
            'email': u.email,
            'is_staff': u.is_staff,
            'is_superuser': u.is_superuser,
            'is_active': u.is_active
        })
    
    return JsonResponse({
        'success': True,
        'message': 'デモユーザーの作成/更新が完了しました',
        'results': results,
        'all_users': all_users,
        'host': request.headers.get('Host', 'unknown')
    }) 