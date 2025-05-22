from django.contrib import admin
from .models import Category, GrapeCheck

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(GrapeCheck)
class GrapeCheckAdmin(admin.ModelAdmin):
    list_display = ('category', 'total_score', 'writing_style_score', 
                   'structure_score', 'keyword_score', 'created_at')
    list_filter = ('category',)
    search_fields = ('content_text', 'improvement_suggestions')
    readonly_fields = ('created_at',)
