"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 5.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
import os
import environ
import ipaddress

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# .envファイルから環境変数を読み込む
env = environ.Env()
env.read_env(BASE_DIR / ".env")
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
# ステージング環境でのデバッグを一時的に有効化（問題解決後に無効化）
DEBUG = True  # 一時的にTrueに変更

# Basic認証設定（本番環境では外部で制御）
BASIC_AUTH_ENABLED = env.bool("BASIC_AUTH_ENABLED", default=False) and not DEBUG

# 環境変数から取得、存在しない場合はワイルドカードを使用
# ECS環境での内部IPアドレスも明示的に許可
ALLOWED_HOSTS_ENV = os.environ.get("ALLOWED_HOSTS", "*")
if ALLOWED_HOSTS_ENV == "*":
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = ALLOWED_HOSTS_ENV.split(",")

# ECS環境での内部アクセスを許可（プライベートサブネット対応）
ALLOWED_HOSTS.extend([
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "staging.grape-app.jp",
    "10.0.1.77",      # 現在のECSタスクIP
    "10.0.1.95",      # 以前のエラーログで確認されたIP
])

# プライベートサブネット全体を許可（10.0.x.x）
def is_private_ip(ip):
    try:
        return ipaddress.ip_address(ip).is_private
    except:
        return False

# リクエスト処理時にプライベートIPを動的に許可
class AllowPrivateIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]  # ポート番号を除去
        if is_private_ip(host) and host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)
        response = self.get_response(request)
        return response

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # allauth required
    # django-allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # 自作アプリケーション
    "core",
    "proofreading_ai",
    "tags",
    "grapecheck",  # グレイプらしさチェッカー
]

MIDDLEWARE = [
    # "core.middleware.BasicAuthMiddleware",  # nginx プロキシでBasic認証を行うため無効化
    "config.settings.AllowPrivateIPMiddleware",  # プライベートIP動的許可
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # allauth required
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "ja"

TIME_ZONE = "Asia/Tokyo"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# django-allauth設定
# 環境に応じてSITE_IDを動的に設定
if DEBUG:
    # ローカル環境では localhost:8000 のサイトを使用（ID: 2）
    SITE_ID = 2
else:
    # 本番・ステージング環境では staging.grape-app.jp のサイトを使用（ID: 1）
    SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    # デフォルトのDjango認証バックエンド
    'django.contrib.auth.backends.ModelBackend',
    # allauth用認証バックエンド
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ログイン・ログアウト後のリダイレクト先
LOGIN_URL = '/accounts/login/'  # 未ログインユーザーのリダイレクト先
LOGIN_REDIRECT_URL = '/dashboard/'  # ログイン後はダッシュボードへ
LOGOUT_REDIRECT_URL = '/'  # ログアウト後はウェルカムページへ

# allauth設定
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'  # 社内利用のため
ACCOUNT_USERNAME_REQUIRED = True  # usernameも使用可能にする
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_SIGNUP_REDIRECT_URL = '/dashboard/'  # 新規登録後もダッシュボードへ
ACCOUNT_LOGIN_REDIRECT_URL = '/dashboard/'   # ログイン後はダッシュボードへ
ACCOUNT_LOGOUT_REDIRECT_URL = '/'  # ログアウト後はウェルカムページへ

# 新規登録を有効化（社内メンバー用テストアカウント作成可能）
ACCOUNT_ALLOW_REGISTRATION = True

# 新しい形式の設定（非推奨警告を解消）
ACCOUNT_LOGIN_METHODS = ['username', 'email']  # ユーザー名とメールの両方でログイン可能
ACCOUNT_SIGNUP_FIELDS = ['email', 'username', 'password1', 'password2']
ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/5m',  # 5回失敗で5分間ロック
}

# Google OAuth設定
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'hd': 'grapee.co.jp',  # Google Workspaceドメイン制限
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

# Social accountの設定
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True  # 自動でアカウント作成（@grapee.co.jpのみ）
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_STORE_TOKENS = True

# セッション設定（認証問題の解決）
SESSION_COOKIE_AGE = 3600  # 1時間でセッション期限切れ
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # ブラウザ閉じたらセッション削除
SESSION_SAVE_EVERY_REQUEST = True  # リクエストごとにセッション更新
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS環境でのみSecureフラグ
SESSION_COOKIE_HTTPONLY = True  # JavaScriptからアクセス不可
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF攻撃対策

# キャッシュ無効化設定
CACHE_MIDDLEWARE_SECONDS = 0  # キャッシュ無効
USE_ETAGS = False  # ETagキャッシュ無効

# セキュリティ設定
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS対応設定（環境変数で制御）
HTTPS_ENABLED = os.environ.get("HTTPS_ENABLED", "False").lower() == "true"

if HTTPS_ENABLED:
    # HTTPS強制設定
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000  # 1年間
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # HTTPS環境でのセッション設定
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HTTPSでのCSRF設定
    CSRF_TRUSTED_ORIGINS = [
        'https://staging.grape-app.jp',
        'https://prod.grapee.co.jp',
        'https://localhost:8000',
    ]
else:
    # HTTP環境での設定（開発・デバッグ用）
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    
    # HTTPでのCSRF設定
    CSRF_TRUSTED_ORIGINS = [
        'http://staging.grape-app.jp',
        'https://staging.grape-app.jp',
        'http://prod.grapee.co.jp',
        'https://prod.grapee.co.jp',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

# @grapee.co.jpドメインのみ許可（拡張ユーザー管理対応）
# ステージング環境テスト用：一時的にデフォルトアダプターを使用
if DEBUG:
    # ローカル環境では拡張アダプターを使用
    SOCIALACCOUNT_ADAPTER = 'core.adapters.ExtendedGrapeeWorkspaceAdapter'
else:
    # ステージング環境では一時的にデフォルトアダプターを使用（デバッグ用）
    SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'

# セッション設定（ログインループ問題解決）
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_NAME = 'grapee_sessionid'
SESSION_COOKIE_AGE = 86400  # 24時間
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# HTTP環境でのセッション設定（本番対応）
SESSION_COOKIE_SECURE = False  # HTTPでも動作するように
SESSION_COOKIE_HTTPONLY = True  # XSS対策
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF対策とブラウザ互換性

# CSRF設定（HTTPS対応により上記で設定済み）
CSRF_COOKIE_SAMESITE = 'Lax'

# ドメイン設定（セッション共有用）
SESSION_COOKIE_DOMAIN = None  # 自動検出
CSRF_COOKIE_DOMAIN = None  # 自動検出

# データベースクエリタイムアウト（大容量テキスト校正対応）
DATABASES['default']['OPTIONS'] = {
    'timeout': 600,  # 10分
}

# キャッシュタイムアウト
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 300,  # 5分
    }
}

# Chatwork通知用ルームID（.envまたは環境変数から取得、なければデフォルト値）
CHATWORK_ROOM_ID = os.environ.get("CHATWORK_ROOM_ID", "372584775")
