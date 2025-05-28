from django.contrib import admin
from .models import (
    ProofreadingRequest, ProofreadingResult, ReplacementDictionary,
    CorrectionV2, CompanyDictionary, GeographicData
)


@admin.register(ProofreadingRequest)
class ProofreadingRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('original_text',)
    readonly_fields = ('created_at',)


@admin.register(ProofreadingResult)
class ProofreadingResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'completion_time', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('corrected_text',)
    readonly_fields = ('created_at',)


@admin.register(ReplacementDictionary)
class ReplacementDictionaryAdmin(admin.ModelAdmin):
    list_display = ('original_word', 'replacement_word', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('original_word', 'replacement_word')
    readonly_fields = ('created_at',)


# 校正AI v2用管理画面

@admin.register(CorrectionV2)
class CorrectionV2Admin(admin.ModelAdmin):
    list_display = ('id', 'category', 'original_text', 'corrected_text', 'confidence', 'severity', 'is_applied', 'created_at')
    list_filter = ('category', 'severity', 'is_applied', 'created_at')
    search_fields = ('original_text', 'corrected_text', 'reason')
    readonly_fields = ('created_at',)
    ordering = ('-created_at', 'position')
    
    fieldsets = (
        ('基本情報', {
            'fields': ('request', 'category', 'severity', 'confidence')
        }),
        ('修正内容', {
            'fields': ('original_text', 'corrected_text', 'reason', 'position')
        }),
        ('状態', {
            'fields': ('is_applied', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('request')


@admin.register(CompanyDictionary)
class CompanyDictionaryAdmin(admin.ModelAdmin):
    list_display = ('term', 'correct_form', 'category', 'priority', 'is_active', 'updated_at')
    list_filter = ('category', 'is_active', 'priority', 'created_at')
    search_fields = ('term', 'correct_form', 'alternative_forms', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-priority', 'term')
    
    fieldsets = (
        ('基本情報', {
            'fields': ('term', 'correct_form', 'alternative_forms', 'category')
        }),
        ('詳細情報', {
            'fields': ('description', 'usage_example')
        }),
        ('設定', {
            'fields': ('priority', 'is_active')
        }),
        ('日時', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_entries', 'deactivate_entries', 'set_high_priority']
    
    def activate_entries(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated}件の辞書エントリを有効にしました。')
    activate_entries.short_description = '選択した辞書エントリを有効にする'
    
    def deactivate_entries(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated}件の辞書エントリを無効にしました。')
    deactivate_entries.short_description = '選択した辞書エントリを無効にする'
    
    def set_high_priority(self, request, queryset):
        updated = queryset.update(priority=10)
        self.message_user(request, f'{updated}件の辞書エントリを高優先度に設定しました。')
    set_high_priority.short_description = '選択した辞書エントリを高優先度に設定'


@admin.register(GeographicData)
class GeographicDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'parent', 'climate_zone', 'is_active', 'created_at')
    list_filter = ('type', 'climate_zone', 'is_active', 'created_at')
    search_fields = ('name', 'characteristics')
    readonly_fields = ('created_at',)
    ordering = ('type', 'name')
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'type', 'parent')
        }),
        ('地理情報', {
            'fields': ('latitude', 'longitude', 'climate_zone')
        }),
        ('特徴', {
            'fields': ('characteristics',)
        }),
        ('設定', {
            'fields': ('is_active', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')
    
    actions = ['activate_data', 'deactivate_data']
    
    def activate_data(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated}件の地理データを有効にしました。')
    activate_data.short_description = '選択した地理データを有効にする'
    
    def deactivate_data(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated}件の地理データを無効にしました。')
    deactivate_data.short_description = '選択した地理データを無効にする' 