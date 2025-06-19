from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Article, SocialMediaUser, ArticleHistory,
    PersonalSNSAccount, CorporateSNSAccount
)


@admin.register(SocialMediaUser)
class SocialMediaUserAdmin(admin.ModelAdmin):
    list_display = [
        'handle_name', 
        'platform', 
        'status_display', 
        'permission_date',
        'permission_expires',
        'created_at'
    ]
    list_filter = ['platform', 'status', 'permission_date']
    search_fields = ['handle_name', 'profile_url', 'notes']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('handle_name', 'platform', 'profile_url')
        }),
        ('許諾情報', {
            'fields': ('status', 'permission_date', 'permission_expires', 'usage_conditions')
        }),
        ('NG情報', {
            'fields': ('ng_reason',),
            'classes': ('collapse',)
        }),
        ('その他', {
            'fields': ('notes',)
        })
    )
    
    def status_display(self, obj):
        """ステータスを色付きで表示"""
        if obj.status == 'ok':
            color = 'green'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'ステータス'


class ArticleHistoryInline(admin.TabularInline):
    """記事履歴のインライン表示"""
    model = ArticleHistory
    extra = 0
    readonly_fields = ['user', 'action', 'old_value', 'new_value', 'created_at']
    can_delete = False


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'article_id',
        'title_truncated',
        'applicant',
        'writer',
        'status_display',
        'created_at',
        'has_ng_users'
    ]
    list_filter = ['status', 'created_at', 'applicant', 'writer']
    search_fields = ['article_id', 'title', 'content', 'reference_url']
    ordering = ['-created_at']
    readonly_fields = ['article_id', 'created_at', 'updated_at', 'approved_at']
    inlines = [ArticleHistoryInline]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('article_id', 'title', 'content', 'reference_url')
        }),
        ('担当者', {
            'fields': ('applicant', 'writer')
        }),
        ('ステータス', {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
        ('SNSユーザー', {
            'fields': ('social_media_users',)
        }),
        ('公開情報', {
            'fields': ('facebook_text', 'published_at')
        }),
        ('その他', {
            'fields': ('notes', 'created_at', 'updated_at')
        })
    )
    
    filter_horizontal = ['social_media_users']
    
    def title_truncated(self, obj):
        """タイトルを50文字で切り詰め"""
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_truncated.short_description = 'タイトル'
    
    def status_display(self, obj):
        """ステータスを色付きで表示"""
        color_map = {
            'draft': '#6B7280',
            'pending': '#F59E0B',
            'rejected': '#EF4444',
            'approved': '#10B981',
            'sent': '#3B82F6',
            'published': '#8B5CF6',
            'unknown': '#6B7280',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color_map.get(obj.status, '#6B7280'),
            obj.get_status_display()
        )
    status_display.short_description = 'ステータス'
    
    def has_ng_users(self, obj):
        """NGユーザーが含まれているか"""
        ng_users = obj.social_media_users.filter(status='ng')
        if ng_users.exists():
            return format_html(
                '<span style="color: red; font-weight: bold;">NG有</span>'
            )
        return format_html(
            '<span style="color: green;">OK</span>'
        )
    has_ng_users.short_description = 'NGユーザー'
    
    def save_model(self, request, obj, form, change):
        """記事保存時に履歴を記録"""
        if change:
            # 変更の場合
            old_obj = Article.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                ArticleHistory.objects.create(
                    article=obj,
                    user=request.user,
                    action='ステータス変更',
                    old_value=old_obj.get_status_display(),
                    new_value=obj.get_status_display()
                )
        else:
            # 新規作成の場合
            obj.save()
            ArticleHistory.objects.create(
                article=obj,
                user=request.user,
                action='記事作成',
                new_value=obj.title
            )
            return
        
        super().save_model(request, obj, form, change)


@admin.register(ArticleHistory)
class ArticleHistoryAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['article__title', 'article__article_id', 'user__username']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        """履歴は手動追加不可"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """履歴は編集不可"""
        return False


@admin.register(PersonalSNSAccount)
class PersonalSNSAccountAdmin(admin.ModelAdmin):
    list_display = ['handle_name', 'platform', 'category', 'status_badge', 'status_date']
    list_filter = ['status', 'platform', 'category', 'status_date']
    search_fields = ['handle_name', 'real_name', 'reason', 'notes']
    ordering = ['handle_name']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('handle_name', 'real_name', 'platform', 'url', 'category')
        }),
        ('ステータス', {
            'fields': ('status', 'reason', 'conditions')
        }),
        ('備考', {
            'fields': ('notes',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'ok': 'green',
            'conditional': 'orange',
            'ng': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'ステータス'


@admin.register(CorporateSNSAccount)
class CorporateSNSAccountAdmin(admin.ModelAdmin):
    list_display = [
        'company_name', 'account_name', 'platform', 
        'overall_status', 'require_prior_approval', 'embed_only'
    ]
    list_filter = [
        'sales_status', 'editorial_status', 'platform', 
        'require_prior_approval', 'embed_only'
    ]
    search_fields = ['company_name', 'account_name', 'primary_contact', 'notes']
    ordering = ['company_name', 'account_name']
    
    fieldsets = (
        ('企業情報', {
            'fields': ('company_name', 'account_name', 'platform', 'url')
        }),
        ('ステータス', {
            'fields': ('sales_status', 'editorial_status')
        }),
        ('利用条件', {
            'fields': (
                'require_prior_approval', 'require_post_report', 'embed_only', 
                'allow_image_download', 'allow_screenshot', 'credit_format',
                'excluded_content', 'special_conditions'
            )
        }),
        ('連絡先', {
            'fields': ('primary_contact', 'pr_agency', 'contact_notes')
        }),
        ('備考', {
            'fields': ('notes',)
        }),
    )
    
    def overall_status(self, obj):
        status = obj.get_overall_status()
        colors = {
            'ok': 'green',
            'checking': 'orange',
            'ng': 'red'
        }
        labels = {
            'ok': 'OK',
            'checking': '確認中',
            'ng': 'NG'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(status, 'black'),
            labels.get(status, status)
        )
    overall_status.short_description = '総合ステータス'
