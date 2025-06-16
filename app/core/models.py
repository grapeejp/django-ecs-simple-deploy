from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    タイムスタンプを持つ抽象基底モデル
    """
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        abstract = True


class AllowedUser(TimeStampedModel):
    """
    認証許可ユーザーモデル
    Google OAuth認証後にアクセスを許可するユーザーを管理
    """
    
    PERMISSION_CHOICES = [
        ('user', '一般ユーザー'),
        ('admin', '管理者'),
        ('superuser', 'スーパーユーザー'),
    ]
    
    email = models.EmailField(unique=True, verbose_name='メールアドレス')
    full_name = models.CharField(max_length=255, verbose_name='氏名')
    department = models.CharField(max_length=100, blank=True, verbose_name='部署')
    permission_level = models.CharField(
        max_length=20, 
        choices=PERMISSION_CHOICES, 
        default='user',
        verbose_name='権限レベル'
    )
    is_active = models.BooleanField(default=True, verbose_name='有効')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='最終ログイン')
    notes = models.TextField(blank=True, verbose_name='備考')
    
    # 関連するDjangoユーザー（OAuth認証後に作成される）
    django_user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Djangoユーザー'
    )
    
    class Meta:
        verbose_name = '認証許可ユーザー'
        verbose_name_plural = '認証許可ユーザー'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def update_last_login(self):
        """最終ログイン時刻を更新"""
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
    
    @property
    def is_admin_or_above(self):
        """管理者権限以上かどうか"""
        return self.permission_level in ['admin', 'superuser']
    
    @property
    def is_superuser(self):
        """スーパーユーザー権限かどうか"""
        return self.permission_level == 'superuser'


class LoginHistory(TimeStampedModel):
    """
    ログイン履歴モデル
    ユーザーのログイン試行を記録（成功・失敗両方）
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    allowed_user = models.ForeignKey(
        AllowedUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='認証許可ユーザー'
    )
    login_time = models.DateTimeField(auto_now_add=True, verbose_name='ログイン時刻')
    ip_address = models.GenericIPAddressField(verbose_name='IPアドレス')
    user_agent = models.TextField(verbose_name='ユーザーエージェント')
    success = models.BooleanField(default=True, verbose_name='成功')
    failure_reason = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name='失敗理由'
    )
    session_key = models.CharField(max_length=40, blank=True, verbose_name='セッションキー')
    
    class Meta:
        verbose_name = 'ログイン履歴'
        verbose_name_plural = 'ログイン履歴'
        ordering = ['-login_time']
    
    def __str__(self):
        status = "成功" if self.success else f"失敗({self.failure_reason})"
        user_name = self.user.get_full_name() or self.user.username
        return f"{user_name} - {self.login_time.strftime('%Y/%m/%d %H:%M')} - {status}"


class UserImportLog(TimeStampedModel):
    """
    ユーザー一括インポートログ
    CSVファイルからのユーザー登録履歴を記録
    """
    
    imported_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='実行者')
    file_name = models.CharField(max_length=255, verbose_name='ファイル名')
    total_records = models.IntegerField(verbose_name='総レコード数')
    success_count = models.IntegerField(verbose_name='成功件数')
    error_count = models.IntegerField(verbose_name='エラー件数')
    error_details = models.TextField(blank=True, verbose_name='エラー詳細')
    
    class Meta:
        verbose_name = 'ユーザーインポートログ'
        verbose_name_plural = 'ユーザーインポートログ'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.file_name} - {self.created_at.strftime('%Y/%m/%d %H:%M')} - {self.success_count}/{self.total_records}件成功" 