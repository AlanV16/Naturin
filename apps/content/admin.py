from django.contrib import admin
from .models import (
    ContentCategory, EducationalSheet, SheetRevisionHistory, StudentContent
)

@admin.register(ContentCategory)
class ContentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(EducationalSheet)
class EducationalSheetAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'difficulty', 'created_at']
    list_filter = ['status', 'difficulty', 'category']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(SheetRevisionHistory)
class SheetRevisionHistoryAdmin(admin.ModelAdmin):
    list_display = ['sheet', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    readonly_fields = ['timestamp']

@admin.register(StudentContent)
class StudentContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'content_type', 'moderation_status', 'created_at']
    list_filter = ['content_type', 'moderation_status']
    search_fields = ['title', 'content']
