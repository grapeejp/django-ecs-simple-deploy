from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


class PersonalSNSAccount(models.Model):
    """個人SNSアカウント管理"""
    
    PLATFORM_CHOICES = [
        ('twitter', 'X (Twitter)'),
        ('instagram', 'Instagram'),
        ('threads', 'Threads'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('blog', 'ブログ'),
    ]
    
    STATUS_CHOICES = [
        ('ok', 'OK（使用可）'),
        ('conditional', '条件付きOK'),
        ('ng', 'NG（使用不可）'),
    ]
    
    CATEGORY_CHOICES = [
        ('manga', '漫画ネタ'),
        ('animal', '動物ネタ'),
        ('celebrity', '芸能人'),
        ('other', 'その他'),
    ]
    
    # 基本情報
    handle_name = models.CharField(
        max_length=100,
        verbose_name='ハンドルネーム'
    )
    real_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='本名'
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        verbose_name='プラットフォーム'
    )
    url = models.URLField(
        verbose_name='プロフィールURL'
    )
    
    # ステータス
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ok',
        verbose_name='ステータス'
    )
    status_date = models.DateField(
        auto_now_add=True,
        verbose_name='ステータス変更日'
    )
    
    # 詳細
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        blank=True,
        verbose_name='カテゴリ'
    )
    reason = models.TextField(
        blank=True,
        verbose_name='NG理由/条件'
    )
    conditions = models.TextField(
        blank=True,
        verbose_name='利用条件'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='備考'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['handle_name', 'platform']
        ordering = ['handle_name']
        verbose_name = '個人SNSアカウント'
        verbose_name_plural = '個人SNSアカウント'
    
    def __str__(self):
        return f"{self.handle_name} ({self.get_platform_display()}) - {self.get_status_display()}"


class CorporateSNSAccount(models.Model):
    """企業SNSアカウント管理"""
    
    STATUS_CHOICES = [
        ('ok', 'OK'),
        ('checking', '確認中'),
        ('ng', 'NG'),
    ]
    
    # 企業情報
    company_name = models.CharField(
        max_length=200,
        verbose_name='企業名'
    )
    account_name = models.CharField(
        max_length=100,
        verbose_name='アカウント名'
    )
    platform = models.CharField(
        max_length=20,
        choices=PersonalSNSAccount.PLATFORM_CHOICES,
        verbose_name='プラットフォーム'
    )
    url = models.URLField(
        verbose_name='URL'
    )
    
    # ステータス（部門別）
    sales_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='checking',
        verbose_name='営業ステータス'
    )
    editorial_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='checking',
        verbose_name='編集ステータス'
    )
    
    # 利用条件フラグ
    require_prior_approval = models.BooleanField(
        default=False,
        verbose_name='事前確認必須'
    )
    require_post_report = models.BooleanField(
        default=False,
        verbose_name='事後報告必須'
    )
    embed_only = models.BooleanField(
        default=False,
        verbose_name='埋め込みのみ'
    )
    allow_image_download = models.BooleanField(
        default=True,
        verbose_name='画像DL可'
    )
    allow_screenshot = models.BooleanField(
        default=True,
        verbose_name='スクショ可'
    )
    
    # 詳細条件
    credit_format = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='クレジット表記形式'
    )
    excluded_content = models.TextField(
        blank=True,
        verbose_name='使用不可コンテンツ'
    )
    special_conditions = models.TextField(
        blank=True,
        verbose_name='特殊条件'
    )
    
    # 連絡先
    primary_contact = models.TextField(
        verbose_name='主要連絡先'
    )
    pr_agency = models.TextField(
        blank=True,
        verbose_name='PR会社情報'
    )
    contact_notes = models.TextField(
        blank=True,
        verbose_name='連絡時の注意事項'
    )
    
    # その他
    notes = models.TextField(
        blank=True,
        verbose_name='補足'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['company_name', 'account_name', 'platform']
        ordering = ['company_name', 'account_name']
        verbose_name = '企業SNSアカウント'
        verbose_name_plural = '企業SNSアカウント'
    
    def __str__(self):
        return f"{self.company_name} - {self.account_name} ({self.get_platform_display()})"
    
    def get_overall_status(self):
        """営業と編集の厳しい方のステータスを返す"""
        if self.sales_status == 'ng' or self.editorial_status == 'ng':
            return 'ng'
        elif self.sales_status == 'checking' or self.editorial_status == 'checking':
            return 'checking'
        return 'ok'


class SocialMediaUser(models.Model):
    """SNSユーザー管理モデル"""
    
    PLATFORM_CHOICES = [
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
    ]
    
    STATUS_CHOICES = [
        ('ok', 'OK（使用可）'),
        ('ng', 'NG（使用不可）'),
    ]
    
    handle_name = models.CharField(
        max_length=100,
        verbose_name='ハンドルネーム',
        help_text='例: @username'
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        verbose_name='プラットフォーム'
    )
    profile_url = models.URLField(
        verbose_name='プロフィールURL',
        blank=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ok',
        verbose_name='ステータス'
    )
    permission_date = models.DateField(
        verbose_name='許諾取得日',
        blank=True,
        null=True
    )
    permission_expires = models.DateField(
        verbose_name='許諾期限',
        blank=True,
        null=True,
        help_text='期限がない場合は空欄'
    )
    usage_conditions = models.TextField(
        verbose_name='利用条件',
        blank=True,
        help_text='クレジット表記など特別な条件'
    )
    ng_reason = models.TextField(
        verbose_name='NG理由',
        blank=True,
        help_text='NGの場合の理由を記載'
    )
    notes = models.TextField(
        verbose_name='備考',
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='登録日時'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新日時'
    )
    
    class Meta:
        verbose_name = 'SNSユーザー'
        verbose_name_plural = 'SNSユーザー'
        unique_together = ['handle_name', 'platform']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_platform_display()} - {self.handle_name} ({self.get_status_display()})"
    
    def is_permission_valid(self):
        """許諾が有効かどうかを確認"""
        if self.status == 'ng':
            return False
        if self.permission_expires and self.permission_expires < timezone.now().date():
            return False
        return True


class Article(models.Model):
    """記事管理モデル"""
    
    STATUS_CHOICES = [
        ('pending', '申請中'),
        ('through', 'スルー'),
        ('ng', '掲載NG'),
        ('need_permission', '要許可'),
        ('no_apply', '申請不要'),
        ('published', '公開済'),
        ('info_provided', '情報提供'),
        ('-', '-'),
        ('post_report', '事後報告'),
        ('original', '独自記事'),
    ]
    
    REPORT_STATUS_CHOICES = [
        ('not_required', '不要'),
        ('sent', '送信済み'),
        ('ready_with_x', '準備完了Xあり'),
        ('ready_without_x', '準備完了Xなし'),
    ]
    
    article_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='記事番号',
        editable=False
    )
    applicant = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='applied_articles',
        verbose_name='申請者'
    )
    writer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='written_articles',
        verbose_name='ライター',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='ステータス'
    )
    report_status = models.CharField(
        max_length=20,
        choices=REPORT_STATUS_CHOICES,
        default='not_required',
        verbose_name='掲載報告'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='記事タイトル'
    )
    content = models.TextField(
        verbose_name='記事内容・概要'
    )
    reference_url = models.URLField(
        verbose_name='参照ネタURL',
        blank=True
    )
    grape_article_url = models.URLField(
        verbose_name='グレイプ記事リンク',
        blank=True
    )
    social_media_id = models.CharField(
        max_length=100,
        verbose_name='ID（IGは手打ち）',
        blank=True
    )
    social_media_users = models.ManyToManyField(
        SocialMediaUser,
        verbose_name='使用SNSユーザー',
        blank=True,
        related_name='articles'
    )
    facebook_text = models.TextField(
        verbose_name='Facebook投稿テキスト',
        blank=True
    )
    notes = models.TextField(
        verbose_name='備考',
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='申請日時'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新日時'
    )
    published_at = models.DateTimeField(
        verbose_name='公開日時',
        blank=True,
        null=True
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='approved_articles',
        verbose_name='承認者',
        blank=True,
        null=True
    )
    approved_at = models.DateTimeField(
        verbose_name='承認日時',
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = '記事'
        verbose_name_plural = '記事'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.article_id} - {self.title}"
    
    def save(self, *args, **kwargs):
        # 新規作成時に記事番号を自動採番
        if not self.article_id:
            last_article = Article.objects.order_by('-article_id').first()
            if last_article and last_article.article_id.isdigit():
                next_id = int(last_article.article_id) + 1
            else:
                # 初回は119500から開始（既存データを考慮）
                next_id = 119500
            self.article_id = str(next_id)
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """バリデーション"""
        # NGユーザーが含まれていないかチェック
        if self.pk:  # 既存レコードの場合のみチェック
            ng_users = self.social_media_users.filter(status='ng')
            if ng_users.exists():
                ng_names = ', '.join([user.handle_name for user in ng_users])
                raise ValidationError(
                    f'NGユーザーが含まれています: {ng_names}'
                )
    
    def get_status_color(self):
        """ステータスに応じた色を返す（UI用）"""
        color_map = {
            'pending': 'warning',
            'through': 'secondary',
            'ng': 'danger',
            'need_permission': 'warning',
            'no_apply': 'info',
            'published': 'success',
            'info_provided': 'primary',
            '-': 'light',
            'post_report': 'info',
            'original': 'dark',
        }
        return color_map.get(self.status, 'secondary')


class ArticleHistory(models.Model):
    """記事の変更履歴"""
    
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='histories',
        verbose_name='記事'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='変更者'
    )
    action = models.CharField(
        max_length=50,
        verbose_name='アクション'
    )
    old_value = models.TextField(
        verbose_name='変更前',
        blank=True
    )
    new_value = models.TextField(
        verbose_name='変更後',
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='変更日時'
    )
    
    class Meta:
        verbose_name = '記事履歴'
        verbose_name_plural = '記事履歴'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.article.article_id} - {self.action} - {self.created_at}"
