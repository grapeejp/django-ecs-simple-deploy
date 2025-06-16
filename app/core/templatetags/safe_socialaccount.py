from django import template
from django.urls import reverse
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.templatetags.socialaccount import provider_login_url
import logging

register = template.Library()
logger = logging.getLogger(__name__)

@register.simple_tag(takes_context=True)
def safe_provider_login_url(context, provider_id, **kwargs):
    """
    安全なプロバイダーログインURL取得
    SocialAppが存在しない場合はNoneを返す
    """
    try:
        request = context['request']
        # SocialAppの存在確認
        if not SocialApp.objects.filter(provider=provider_id).exists():
            logger.warning(f"SocialApp for provider '{provider_id}' not found")
            return None
        
        # 通常のprovider_login_urlを呼び出し
        return provider_login_url(context, provider_id, **kwargs)
    except Exception as e:
        logger.error(f"Error getting provider login URL for {provider_id}: {e}")
        return None

@register.simple_tag
def has_social_provider(provider_id):
    """
    指定されたプロバイダーのSocialAppが存在するかチェック
    """
    try:
        return SocialApp.objects.filter(provider=provider_id).exists()
    except Exception as e:
        logger.error(f"Error checking social provider {provider_id}: {e}")
        return False 