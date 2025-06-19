import re
from urllib.parse import urlparse
from .models import PersonalSNSAccount, CorporateSNSAccount


class SNSAccountChecker:
    """SNSアカウントの利用可否をチェックするユーティリティ"""
    
    @staticmethod
    def detect_platform(url):
        """URLからプラットフォームを判定"""
        if not url:
            return None
            
        url_lower = url.lower()
        if 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'threads.com' in url_lower:
            return 'threads'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif any(x in url_lower for x in ['.blog', 'blog.', 'ameblo']):
            return 'blog'
        return 'website'
    
    @staticmethod
    def extract_handle(url, platform):
        """URLからハンドル名を抽出"""
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            if platform == 'twitter':
                # twitter.com/username or x.com/username
                if len(path_parts) > 0:
                    return path_parts[0].replace('@', '')
            
            elif platform == 'instagram':
                # instagram.com/username/
                if len(path_parts) > 0:
                    return path_parts[0].replace('@', '')
            
            elif platform == 'youtube':
                # youtube.com/@username or youtube.com/channel/...
                if len(path_parts) > 0:
                    if path_parts[0].startswith('@'):
                        return path_parts[0]
                    elif len(path_parts) > 1 and path_parts[0] == 'channel':
                        return path_parts[1]
            
            elif platform == 'tiktok':
                # tiktok.com/@username
                if len(path_parts) > 0 and path_parts[0].startswith('@'):
                    return path_parts[0]
            
        except:
            pass
        
        return None
    
    @classmethod
    def check_url(cls, url):
        """
        URLをチェックして利用可否を返す
        
        Returns:
            dict: {
                'type': 'personal' | 'corporate' | 'unknown',
                'status': 'ok' | 'conditional' | 'ng' | 'checking' | 'unknown',
                'account': モデルインスタンス | None,
                'message': str,
                'conditions': list,
                'contact': str | None
            }
        """
        if not url:
            return {
                'type': 'unknown',
                'status': 'unknown',
                'account': None,
                'message': 'URLが指定されていません',
                'conditions': [],
                'contact': None
            }
        
        # プラットフォームを判定
        platform = cls.detect_platform(url)
        
        # URLの一部でマッチング
        url_parts = url.lower()
        
        # 個人アカウントチェック
        personal_accounts = PersonalSNSAccount.objects.filter(
            platform=platform
        ) if platform else PersonalSNSAccount.objects.all()
        
        for account in personal_accounts:
            # URL完全一致
            if account.url and account.url.lower() == url.lower():
                return cls._format_personal_response(account)
            
            # ハンドル名で部分一致
            if account.handle_name.lower() in url_parts:
                return cls._format_personal_response(account)
        
        # 企業アカウントチェック
        corporate_accounts = CorporateSNSAccount.objects.filter(
            platform=platform
        ) if platform else CorporateSNSAccount.objects.all()
        
        for account in corporate_accounts:
            # URL完全一致
            if account.url and account.url.lower() == url.lower():
                return cls._format_corporate_response(account)
            
            # アカウント名で部分一致
            if account.account_name.lower() in url_parts:
                return cls._format_corporate_response(account)
        
        # 見つからない場合
        return {
            'type': 'unknown',
            'status': 'unknown',
            'account': None,
            'message': '登録されていないアカウントです',
            'conditions': [],
            'contact': None
        }
    
    @staticmethod
    def _format_personal_response(account):
        """個人アカウントのレスポンスをフォーマット"""
        message = ''
        conditions = []
        
        if account.status == 'ng':
            message = f'使用不可: {account.reason}' if account.reason else '使用不可'
        elif account.status == 'conditional':
            message = '条件付きで使用可能'
            if account.conditions:
                conditions = [account.conditions]
        else:
            message = '使用可能'
        
        return {
            'type': 'personal',
            'status': account.status,
            'account': account,
            'message': message,
            'conditions': conditions,
            'contact': None
        }
    
    @staticmethod
    def _format_corporate_response(account):
        """企業アカウントのレスポンスをフォーマット"""
        status = account.get_overall_status()
        conditions = []
        
        # 条件をリスト化
        if account.require_prior_approval:
            conditions.append('事前確認必須')
        if account.require_post_report:
            conditions.append('事後報告必須')
        if account.embed_only:
            conditions.append('埋め込みのみ')
        if not account.allow_image_download:
            conditions.append('画像DL不可')
        if not account.allow_screenshot:
            conditions.append('スクショ不可')
        if account.credit_format:
            conditions.append(f'クレジット表記: {account.credit_format}')
        
        message_parts = []
        if status == 'ng':
            message_parts.append('使用不可')
        elif status == 'checking':
            message_parts.append('確認中')
        else:
            if conditions:
                message_parts.append('条件付きで使用可能')
            else:
                message_parts.append('使用可能')
        
        if account.special_conditions:
            message_parts.append(account.special_conditions[:100] + '...' if len(account.special_conditions) > 100 else account.special_conditions)
        
        return {
            'type': 'corporate',
            'status': 'conditional' if status == 'ok' and conditions else status,
            'account': account,
            'message': ' / '.join(message_parts),
            'conditions': conditions,
            'contact': account.primary_contact
        }