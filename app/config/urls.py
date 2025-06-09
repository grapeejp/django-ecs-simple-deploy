"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from health_check import health_check
import sys
import os

# welcome_viewをインポートするためにappディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from welcome_view import welcome

urlpatterns = [
    # path("", welcome, name="welcome"),  # コメントアウト
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path('accounts/', include('allauth.urls')),  # django-allauth
    path('', include('core.urls')),  # ダッシュボード
    path('proofreading_ai/', include('proofreading_ai.urls')),  # 校正AIアプリ
    path('tags/', include('tags.urls')),  # タグ推薦アプリ
    path('grapecheck/', include('grapecheck.urls')),  # グレイプらしさチェッカー
]
