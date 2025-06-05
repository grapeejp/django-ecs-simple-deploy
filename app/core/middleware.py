import base64
import os
import logging
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

# ログ設定
logger = logging.getLogger(__name__)

class BasicAuthMiddleware(MiddlewareMixin):
    """
    Basic認証ミドルウェア
    ステージング環境でのアクセス制御に使用
    """

    def process_request(self, request):
        # 必ずログに出力されるようにprint文も追加
        print("🚨🚨🚨 BasicAuthMiddleware: process_request called 🚨🚨🚨")
        logger.error("🚨🚨🚨 BasicAuthMiddleware: process_request called 🚨🚨🚨")
        
        # Basic認証が無効化されている場合はスキップ
        basic_auth_enabled = os.environ.get('BASIC_AUTH_ENABLED', '')
        print(f"🚨 BASIC_AUTH_ENABLED: '{basic_auth_enabled}'")
        logger.error(f"🚨 BASIC_AUTH_ENABLED: '{basic_auth_enabled}'")
        
        if not basic_auth_enabled.lower() == 'true':
            print("🚨 Basic認証が無効のためスキップ")
            logger.error("🚨 Basic認証が無効のためスキップ")
            return None

        # Basic認証の設定を取得
        basic_username = os.environ.get('BASIC_AUTH_USERNAME', '')
        basic_password = os.environ.get('BASIC_AUTH_PASSWORD', '')
        print(f"🚨 BASIC_AUTH_USERNAME: '{basic_username}'")
        print(f"🚨 BASIC_AUTH_PASSWORD: {'*' * len(basic_password) if basic_password else 'None'}")
        logger.error(f"🚨 BASIC_AUTH_USERNAME: '{basic_username}'")
        logger.error(f"🚨 BASIC_AUTH_PASSWORD: {'*' * len(basic_password) if basic_password else 'None'}")
        
        # 設定が不完全な場合はスキップ
        if not basic_username or not basic_password:
            print("🚨 Basic認証の設定が不完全のためスキップ")
            logger.error("🚨 Basic認証の設定が不完全のためスキップ")
            return None

        # Authorizationヘッダーを確認
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        print(f"🚨 Authorization header: '{auth_header[:50]}...' (truncated)" if auth_header else "🚨 Authorization header: None")
        logger.error(f"🚨 Authorization header: '{auth_header[:50]}...' (truncated)" if auth_header else "🚨 Authorization header: None")
        
        if not auth_header.startswith('Basic '):
            print("🚨🚨🚨 Basic認証ヘッダーがないため401を返す 🚨🚨🚨")
            logger.error("🚨🚨🚨 Basic認証ヘッダーがないため401を返す 🚨🚨🚨")
            return self._require_auth()

        # Basic認証の値を取得
        try:
            auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
            username, password = auth_decoded.split(':', 1)
            print(f"🚨 認証試行: username='{username}'")
            logger.error(f"🚨 認証試行: username='{username}'")
        except (ValueError, UnicodeDecodeError):
            print("🚨🚨🚨 Basic認証ヘッダーのデコードに失敗 🚨🚨🚨")
            logger.error("🚨🚨🚨 Basic認証ヘッダーのデコードに失敗 🚨🚨🚨")
            return self._require_auth()

        # 認証情報を検証
        if username == basic_username and password == basic_password:
            print("✅ Basic認証成功")
            logger.error("✅ Basic認証成功")
            return None  # 認証成功
        else:
            print("🚨🚨🚨 Basic認証失敗 🚨🚨🚨")
            logger.error("🚨🚨🚨 Basic認証失敗 🚨🚨🚨")
            return self._require_auth()

    def _require_auth(self):
        """Basic認証を要求するレスポンスを返す"""
        print("🚨🚨🚨 401レスポンスを返します 🚨🚨🚨")
        logger.error("🚨🚨🚨 401レスポンスを返します 🚨🚨🚨")
        response = HttpResponse('認証が必要です。正しいユーザー名とパスワードを入力してください。', status=401)
        response['WWW-Authenticate'] = 'Basic realm="Django ECS App - Authentication Required"'
        response['Content-Type'] = 'text/plain; charset=utf-8'
        return response