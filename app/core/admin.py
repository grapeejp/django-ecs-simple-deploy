from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AllowedUser, LoginHistory, UserImportLog


@admin.register(AllowedUser)
class AllowedUserAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 
        'email', 
        'department', 
        'permission_level', 
        'is_active', 
        'last_login_display',
        'created_at'
    ]
    list_filter = ['permission_level', 'is_active', 'department', 'created_at']
    search_fields = ['full_name', 'email', 'department']
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    list_editable = ['is_active', 'permission_level']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('email', 'full_name', 'department')
        }),
        ('権限設定', {
            'fields': ('permission_level', 'is_active')
        }),
        ('関連情報', {
            'fields': ('django_user', 'notes')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_users', 'deactivate_users', 'make_admin', 'make_user']
    
    def last_login_display(self, obj):
        """最終ログイン時刻の表示"""
        if obj.last_login:
            return obj.last_login.strftime('%Y/%m/%d %H:%M')
        return '-'
    last_login_display.short_description = '最終ログイン'
    
    def activate_users(self, request, queryset):
        """ユーザーを有効化"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated}人のユーザーを有効化しました。')
    activate_users.short_description = '選択したユーザーを有効化'
    
    def deactivate_users(self, request, queryset):
        """ユーザーを無効化"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated}人のユーザーを無効化しました。')
    deactivate_users.short_description = '選択したユーザーを無効化'
    
    def make_admin(self, request, queryset):
        """管理者権限に変更"""
        updated = queryset.update(permission_level='admin')
        self.message_user(request, f'{updated}人のユーザーを管理者に変更しました。')
    make_admin.short_description = '選択したユーザーを管理者に変更'
    
    def make_user(self, request, queryset):
        """一般ユーザー権限に変更"""
        updated = queryset.update(permission_level='user')
        self.message_user(request, f'{updated}人のユーザーを一般ユーザーに変更しました。')
    make_user.short_description = '選択したユーザーを一般ユーザーに変更'


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'user_display',
        'login_time',
        'success_display',
        'ip_address',
        'user_agent_short'
    ]
    list_filter = ['success', 'login_time']
    search_fields = ['user__username', 'user__email', 'ip_address']
    readonly_fields = ['user', 'allowed_user', 'login_time', 'ip_address', 'user_agent', 'success', 'failure_reason', 'session_key']
    date_hierarchy = 'login_time'
    
    def has_add_permission(self, request):
        """追加権限を無効化（ログは自動生成のため）"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """変更権限を無効化（ログは変更不可）"""
        return False
    
    def user_display(self, obj):
        """ユーザー表示"""
        return obj.user.get_full_name() or obj.user.username
    user_display.short_description = 'ユーザー'
    
    def success_display(self, obj):
        """成功/失敗の表示"""
        if obj.success:
            return format_html('<span style="color: green;">✓ 成功</span>')
        else:
            return format_html('<span style="color: red;">✗ 失敗 ({})</span>', obj.failure_reason)
    success_display.short_description = '結果'
    
    def user_agent_short(self, obj):
        """ユーザーエージェントの短縮表示"""
        if len(obj.user_agent) > 50:
            return obj.user_agent[:50] + '...'
        return obj.user_agent
    user_agent_short.short_description = 'ユーザーエージェント'


@admin.register(UserImportLog)
class UserImportLogAdmin(admin.ModelAdmin):
    list_display = [
        'file_name',
        'imported_by',
        'created_at',
        'success_rate_display',
        'total_records'
    ]
    list_filter = ['created_at', 'imported_by']
    search_fields = ['file_name', 'imported_by__username']
    readonly_fields = ['imported_by', 'created_at', 'file_name', 'total_records', 'success_count', 'error_count', 'error_details']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        """追加権限を無効化（ログは自動生成のため）"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """変更権限を無効化（ログは変更不可）"""
        return False
    
    def success_rate_display(self, obj):
        """成功率の表示"""
        if obj.total_records > 0:
            rate = (obj.success_count / obj.total_records) * 100
            color = 'green' if rate == 100 else 'orange' if rate >= 80 else 'red'
            return format_html(
                '<span style="color: {};">{}/{} ({:.1f}%)</span>',
                color, obj.success_count, obj.total_records, rate
            )
        return '-'
    success_rate_display.short_description = '成功率' 