import base64
import os
from functools import wraps
from django.http import HttpResponse

def basic_auth_required(view_func):
    """
    Basic認証を必須とするデコレータ
    環境変数でBasic認証が有効な場合のみ認証を要求
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print("🚨🚨🚨 basic_auth_required decorator called 🚨🚨🚨")
        
        # Basic認証が無効化されている場合はスキップ
        basic_auth_enabled = os.environ.get('BASIC_AUTH_ENABLED', '')
        print(f"🚨 BASIC_AUTH_ENABLED: '{basic_auth_enabled}'")
        
        if not basic_auth_enabled.lower() == 'true':
            print("🚨 Basic認証が無効のためスキップ")
            return view_func(request, *args, **kwargs)

        # Basic認証の設定を取得
        basic_username = os.environ.get('BASIC_AUTH_USERNAME', '')
        basic_password = os.environ.get('BASIC_AUTH_PASSWORD', '')
        print(f"🚨 BASIC_AUTH_USERNAME: '{basic_username}'")
        print(f"🚨 BASIC_AUTH_PASSWORD: {'*' * len(basic_password) if basic_password else 'None'}")
        
        # 設定が不完全な場合はスキップ
        if not basic_username or not basic_password:
            print("🚨 Basic認証の設定が不完全のためスキップ")
            return view_func(request, *args, **kwargs)

        # Authorizationヘッダーを確認
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        print(f"🚨 Authorization header: '{auth_header[:50]}...' (truncated)" if auth_header else "🚨 Authorization header: None")
        
        if not auth_header.startswith('Basic '):
            print("🚨🚨🚨 Basic認証ヘッダーがないため401を返す 🚨🚨🚨")
            return _require_auth()

        # Basic認証の値を取得
        try:
            auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
            username, password = auth_decoded.split(':', 1)
            print(f"🚨 認証試行: username='{username}'")
        except (ValueError, UnicodeDecodeError):
            print("🚨🚨🚨 Basic認証ヘッダーのデコードに失敗 🚨🚨🚨")
            return _require_auth()

        # 認証情報を検証
        if username == basic_username and password == basic_password:
            print("✅ Basic認証成功")
            return view_func(request, *args, **kwargs)  # 認証成功
        else:
            print("🚨🚨🚨 Basic認証失敗 🚨🚨🚨")
            return _require_auth()

    return wrapper

def _require_auth():
    """Basic認証を要求するレスポンスを返す"""
    print("🚨🚨🚨 401レスポンスを返します 🚨🚨🚨")
    response = HttpResponse('認証が必要です。正しいユーザー名とパスワードを入力してください。', status=401)
    response['WWW-Authenticate'] = 'Basic realm="Django ECS App - Authentication Required"'
    response['Content-Type'] = 'text/plain; charset=utf-8'
    return response 