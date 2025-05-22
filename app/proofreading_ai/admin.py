from django.contrib import admin
from .models import ProofreadingRequest, ProofreadingResult, ReplacementDictionary


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