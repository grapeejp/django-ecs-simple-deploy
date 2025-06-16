from django.http import HttpResponse
from django.shortcuts import redirect


def welcome(request):
    """
    認証状態に応じてリダイレクトするビュー
    - 認証済みユーザー: ダッシュボードにリダイレクト
    - 未認証ユーザー: ログインページにリダイレクト
    """
    # 認証済みユーザーはダッシュボードにリダイレクト
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # 未認証ユーザーはログインページにリダイレクト
    return redirect('account_login')
