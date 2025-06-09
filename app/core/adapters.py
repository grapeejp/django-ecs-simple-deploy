from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


class GrapeeWorkspaceAdapter(DefaultSocialAccountAdapter):
    """
    @grapee.co.jpドメインのみを許可するGoogle Workspaceアダプター
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        ソーシャルログイン前にドメインチェックを実行
        """
        # Googleプロバイダーのみチェック
        if sociallogin.account.provider == 'google':
            email = sociallogin.account.extra_data.get('email', '')
            logger.info(f"Google OAuth認証試行: {email}")
            print(f"DEBUG: Google OAuth認証試行: {email}")
            
            # @grapee.co.jpドメインかチェック
            if not email.endswith('@grapee.co.jp'):
                logger.warning(f"ドメイン制限により認証拒否: {email}")
                print(f"DEBUG: ドメイン制限により認証拒否: {email}")
                messages.error(
                    request,
                    f'グレイプ社内ツールには@grapee.co.jpのアカウントでのみログインできます。\n'
                    f'使用されたアカウント: {email}'
                )
                # ログインページにリダイレクト
                raise ImmediateHttpResponse(
                    HttpResponseRedirect(reverse('account_login'))
                )
            else:
                logger.info(f"ドメイン認証成功: {email}")
                print(f"DEBUG: ドメイン認証成功: {email}")
    
    def is_open_for_signup(self, request, sociallogin):
        """
        @grapee.co.jpドメインのみ新規登録を許可
        """
        if sociallogin.account.provider == 'google':
            email = sociallogin.account.extra_data.get('email', '')
            result = email.endswith('@grapee.co.jp')
            logger.info(f"新規登録チェック - Email: {email}, 許可: {result}")
            print(f"DEBUG: 新規登録チェック - Email: {email}, 許可: {result}")
            return result
        return False 