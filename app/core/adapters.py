from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
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
            print(f"DEBUG: extra_data = {sociallogin.account.extra_data}")
            
            # メールアドレスが取得できない場合のエラーハンドリング
            if not email:
                logger.error("メールアドレスが取得できませんでした")
                print("DEBUG: メールアドレスが取得できませんでした")
                messages.error(
                    request,
                    '認証エラー: Googleアカウントからメールアドレスを取得できませんでした。\n'
                    'Google OAuth設定を確認してください。'
                )
                raise ImmediateHttpResponse(
                    HttpResponseRedirect(reverse('account_login'))
                )
            
            # @grapee.co.jpドメインかチェック
            if not email.endswith('@grapee.co.jp'):
                logger.warning(f"ドメイン制限により認証拒否: {email}")
                print(f"DEBUG: ドメイン制限により認証拒否: {email}")
                messages.error(
                    request,
                    f'❌ ドメイン制限エラー\n\n'
                    f'グレイプ社内ツールには@grapee.co.jpのアカウントでのみログインできます。\n\n'
                    f'🔍 使用されたアカウント: {email}\n'
                    f'✅ 必要なドメイン: @grapee.co.jp\n\n'
                    f'正しいアカウントでログインし直してください。'
                )
                # ログインページにリダイレクト
                raise ImmediateHttpResponse(
                    HttpResponseRedirect(reverse('account_login'))
                )
            else:
                logger.info(f"ドメイン認証成功: {email}")
                print(f"DEBUG: ドメイン認証成功: {email}")
                
                # 追加のデバッグ情報
                print(f"DEBUG: 認証成功 - ユーザー情報:")
                print(f"  - Email: {email}")
                print(f"  - Name: {sociallogin.account.extra_data.get('name', 'N/A')}")
                print(f"  - Provider: {sociallogin.account.provider}")
                print(f"  - UID: {sociallogin.account.uid}")
    
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
    
    def populate_user(self, request, sociallogin, data):
        """
        ユーザー情報の設定（デバッグ情報付き）
        """
        user = super().populate_user(request, sociallogin, data)
        
        # デバッグ情報を出力
        print(f"DEBUG: populate_user called:")
        print(f"  - User: {user}")
        print(f"  - Email: {user.email}")
        print(f"  - Username: {user.username}")
        print(f"  - Data: {data}")
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        ユーザー保存（デバッグ情報付き）
        """
        print(f"DEBUG: save_user called for {sociallogin.account.extra_data.get('email')}")
        
        user = super().save_user(request, sociallogin, form)
        
        print(f"DEBUG: User saved successfully:")
        print(f"  - ID: {user.id}")
        print(f"  - Email: {user.email}")
        print(f"  - Username: {user.username}")
        print(f"  - Is Active: {user.is_active}")
        
        return user


class ExtendedGrapeeWorkspaceAdapter(DefaultSocialAccountAdapter):
    """
    AllowedUserモデルを使用する拡張Google Workspaceアダプター
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        ソーシャルログイン前にAllowedUserチェックを実行
        """
        # Googleプロバイダーのみチェック
        if sociallogin.account.provider == 'google':
            email = sociallogin.account.extra_data.get('email', '')
            logger.info(f"Google OAuth認証試行: {email}")
            
            # 基本的なドメインチェック
            if not email.endswith('@grapee.co.jp'):
                self._handle_auth_failure(
                    request, 
                    email, 
                    f'グレイプ社内ツールには@grapee.co.jpのアカウントでのみログインできます。\n使用されたアカウント: {email}',
                    'domain_restriction'
                )
                return
            
            # AllowedUserチェック
            try:
                from .models import AllowedUser
                allowed_user = AllowedUser.objects.get(email=email, is_active=True)
                logger.info(f"認証許可ユーザー確認成功: {email} (権限: {allowed_user.permission_level})")
                
                # 既存のDjangoユーザーとの関連付けチェック
                if not allowed_user.django_user:
                    # 既存のDjangoユーザーを検索
                    from django.contrib.auth.models import User
                    existing_user = User.objects.filter(email=email).first()
                    if existing_user:
                        logger.info(f"既存Djangoユーザーと関連付け: {email}")
                        allowed_user.django_user = existing_user
                        allowed_user.save()
                
                # リクエストにAllowedUserを保存（後で使用）
                request.session['allowed_user_id'] = allowed_user.id
                
            except AllowedUser.DoesNotExist:
                self._handle_auth_failure(
                    request,
                    email,
                    f'申し訳ございませんが、{email} はシステムへのアクセスが許可されていません。\n'
                    f'アクセスが必要な場合は、システム管理者にお問い合わせください。',
                    'user_not_allowed'
                )
                return
    
    def save_user(self, request, sociallogin, form=None):
        """
        ユーザー保存時にAllowedUserとの関連付けを行う
        """
        user = super().save_user(request, sociallogin, form)
        
        # AllowedUserとの関連付け
        allowed_user_id = request.session.get('allowed_user_id')
        if allowed_user_id:
            try:
                from .models import AllowedUser
                allowed_user = AllowedUser.objects.get(id=allowed_user_id)
                
                # AllowedUserにDjangoユーザーを関連付け
                allowed_user.django_user = user
                allowed_user.update_last_login()
                allowed_user.save()
                
                # ユーザーの基本情報を更新
                if allowed_user.full_name and not user.get_full_name():
                    name_parts = allowed_user.full_name.split(' ', 1)
                    user.first_name = name_parts[0]
                    if len(name_parts) > 1:
                        user.last_name = name_parts[1]
                    user.save()
                
                # ログイン履歴を記録
                self._record_login_history(request, user, allowed_user, True)
                
                logger.info(f"ユーザー関連付け成功: {user.email} -> AllowedUser ID: {allowed_user.id}")
                
            except AllowedUser.DoesNotExist:
                logger.error(f"AllowedUser not found for ID: {allowed_user_id}")
        
        return user
    
    def is_open_for_signup(self, request, sociallogin):
        """
        AllowedUserに登録されている@grapee.co.jpドメインのみ新規登録を許可
        """
        if sociallogin.account.provider == 'google':
            email = sociallogin.account.extra_data.get('email', '')
            
            # ドメインチェック
            if not email.endswith('@grapee.co.jp'):
                return False
            
            # AllowedUserチェック
            try:
                from .models import AllowedUser
                allowed_user = AllowedUser.objects.get(email=email, is_active=True)
                logger.info(f"新規登録許可 - Email: {email}, AllowedUser: {allowed_user.full_name}")
                return True
            except AllowedUser.DoesNotExist:
                logger.warning(f"新規登録拒否 - Email: {email} (AllowedUserに未登録)")
                return False
        
        return False
    
    def _handle_auth_failure(self, request, email, message, reason):
        """
        認証失敗時の共通処理
        """
        logger.warning(f"認証失敗: {email} - {reason}")
        
        # 失敗ログを記録（ユーザーが存在しない場合もあるため、try-except）
        try:
            user = User.objects.filter(email=email).first()
            if user:
                self._record_login_history(request, user, None, False, reason)
        except Exception as e:
            logger.error(f"ログイン履歴記録エラー: {e}")
        
        messages.error(request, message)
        raise ImmediateHttpResponse(
            HttpResponseRedirect(reverse('account_login'))
        )
    
    def _record_login_history(self, request, user, allowed_user, success, failure_reason=''):
        """
        ログイン履歴を記録
        """
        try:
            from .models import LoginHistory
            
            # IPアドレスを取得
            ip_address = self._get_client_ip(request)
            
            # ユーザーエージェントを取得
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # セッションキーを取得
            session_key = request.session.session_key or ''
            
            LoginHistory.objects.create(
                user=user,
                allowed_user=allowed_user,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                failure_reason=failure_reason,
                session_key=session_key
            )
            
            logger.info(f"ログイン履歴記録: {user.email} - {'成功' if success else '失敗'}")
            
        except Exception as e:
            logger.error(f"ログイン履歴記録エラー: {e}")
    
    def _get_client_ip(self, request):
        """
        クライアントのIPアドレスを取得
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '127.0.0.1' 