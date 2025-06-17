from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
import logging
import traceback

logger = logging.getLogger(__name__)


class GrapeeWorkspaceAdapter(DefaultSocialAccountAdapter):
    """
    @grapee.co.jpドメインのみを許可するGoogle Workspaceアダプター
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        ソーシャルログイン前にドメインチェックを実行
        """
        try:
            # Googleプロバイダーのみチェック
            if sociallogin.account.provider == 'google':
                # デバッグ情報をログに記録
                logger.info(f"=== Google OAuth Debug Info ===")
                logger.info(f"Provider: {sociallogin.account.provider}")
                logger.info(f"Extra data keys: {list(sociallogin.account.extra_data.keys())}")
                logger.info(f"Full extra data: {sociallogin.account.extra_data}")
                
                email = sociallogin.account.extra_data.get('email', '')
                logger.info(f"Google OAuth認証試行: {email}")
                print(f"DEBUG: Google OAuth認証試行: {email}")
                
                if not email:
                    error_msg = "Googleアカウントからメールアドレスを取得できませんでした"
                    logger.error(error_msg)
                    print(f"ERROR: {error_msg}")
                    messages.error(request, f"認証エラー: {error_msg}")
                    raise ImmediateHttpResponse(HttpResponseRedirect(reverse('account_login')))
                
                if not email.endswith('@grapee.co.jp'):
                    error_msg = f"@grapee.co.jpドメインのアカウントのみ利用可能です（試行されたアカウント: {email}）"
                    logger.warning(error_msg)
                    print(f"WARNING: {error_msg}")
                    messages.error(request, f"認証エラー: {error_msg}")
                    raise ImmediateHttpResponse(HttpResponseRedirect(reverse('account_login')))
                
                logger.info(f"ドメインチェック通過: {email}")
                print(f"SUCCESS: ドメインチェック通過: {email}")
                
        except ImmediateHttpResponse:
            # 既にエラーレスポンスが設定されている場合は再発生
            raise
        except Exception as e:
            error_msg = f"認証処理中にエラーが発生しました: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            print(f"EXCEPTION: {error_msg}")
            print(f"TRACEBACK: {traceback.format_exc()}")
            messages.error(request, f"システムエラー: {error_msg}")
            raise ImmediateHttpResponse(HttpResponseRedirect(reverse('account_login')))

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
    @grapee.co.jpドメイン + AllowedUserテーブルでの制限を行うアダプター
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        ソーシャルログイン前にドメインチェックとAllowedUserチェックを実行
        """
        try:
            # Googleプロバイダーのみチェック
            if sociallogin.account.provider == 'google':
                email = sociallogin.account.extra_data.get('email', '')
                logger.info(f"Extended Google OAuth認証試行: {email}")
                print(f"DEBUG: Extended Google OAuth認証試行: {email}")
                
                if not email:
                    error_msg = "Googleアカウントからメールアドレスを取得できませんでした"
                    logger.error(error_msg)
                    print(f"ERROR: {error_msg}")
                    messages.error(request, f"認証エラー: {error_msg}")
                    raise ImmediateHttpResponse(HttpResponseRedirect(reverse('account_login')))
                
                if not email.endswith('@grapee.co.jp'):
                    error_msg = f"@grapee.co.jpドメインのアカウントのみ利用可能です（試行されたアカウント: {email}）"
                    logger.warning(error_msg)
                    print(f"WARNING: {error_msg}")
                    messages.error(request, f"認証エラー: {error_msg}")
                    raise ImmediateHttpResponse(HttpResponseRedirect(reverse('account_login')))
                
                # AllowedUserテーブルでのチェック
                from core.models import AllowedUser
                try:
                    allowed_user = AllowedUser.objects.get(email=email)
                    if not allowed_user.is_active:
                        error_msg = f"アカウント {email} は現在無効化されています"
                        logger.warning(error_msg)
                        print(f"WARNING: {error_msg}")
                        messages.error(request, f"認証エラー: {error_msg}")
                        raise ImmediateHttpResponse(HttpResponseRedirect(reverse('account_login')))
                    
                    logger.info(f"AllowedUser確認完了: {email} (管理者権限: {allowed_user.is_admin})")
                    print(f"SUCCESS: AllowedUser確認完了: {email}")
                    
                except AllowedUser.DoesNotExist:
                    error_msg = f"アカウント {email} は登録されていません。管理者にお問い合わせください"
                    logger.warning(error_msg)
                    print(f"WARNING: {error_msg}")
                    messages.error(request, f"認証エラー: {error_msg}")
                    raise ImmediateHttpResponse(HttpResponseRedirect(reverse('account_login')))
                
        except ImmediateHttpResponse:
            # 既にエラーレスポンスが設定されている場合は再発生
            raise
        except Exception as e:
            error_msg = f"認証処理中にエラーが発生しました: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            print(f"EXCEPTION: {error_msg}")
            print(f"TRACEBACK: {traceback.format_exc()}")
            messages.error(request, f"システムエラー: {error_msg}")
            raise ImmediateHttpResponse(HttpResponseRedirect(reverse('account_login')))
    
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