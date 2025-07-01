from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import MultimediaCard, MultimediaTag, MultimediaCardTag


@admin.register(MultimediaTag)
class MultimediaTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'multimedia_count']
    search_fields = ['name']
    list_filter = ['name']
    
    def color_display(self, obj):
        return format_html(
            '<div style="background-color: {}; width: 20px; height: 20px; border-radius: 3px;"></div>',
            obj.color
        )
    color_display.short_description = 'Color'
    
    def multimedia_count(self, obj):
        return obj.multimediacard_set.count()
    multimedia_count.short_description = 'Fichas asociadas'


class MultimediaCardTagInline(admin.TabularInline):
    model = MultimediaCardTag
    extra = 1


@admin.register(MultimediaCard)
class MultimediaCardAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'media_type', 'category', 'author', 'educational_level', 
        'is_public', 'is_featured', 'views_count', 'downloads_count', 'created_at'
    ]
    list_filter = [
        'media_type', 'educational_level', 'category', 'is_public', 
        'is_featured', 'created_at', 'author'
    ]
    search_fields = ['title', 'description', 'subject_area', 'author__username']
    readonly_fields = ['views_count', 'downloads_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información básica', {
            'fields': ('title', 'description', 'media_type')
        }),
        ('Archivos multimedia', {
            'fields': ('video_file', 'audio_file', 'image_file', 'document_file', 'external_url'),
            'classes': ('collapse',)
        }),
        ('Metadatos educativos', {
            'fields': ('educational_level', 'subject_area', 'learning_objectives', 'duration')
        }),
        ('Clasificación', {
            'fields': ('category', 'locations')
        }),
        ('Configuración', {
            'fields': ('author', 'is_public', 'is_featured')
        }),
        ('Estadísticas', {
            'fields': ('views_count', 'downloads_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [MultimediaCardTagInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'author').prefetch_related('locations')
    
    def media_preview(self, obj):
        """Muestra una vista previa del contenido multimedia"""
        if obj.media_type == 'image' and obj.image_file:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.image_file.url
            )
        elif obj.media_type == 'video' and obj.video_file:
            return format_html(
                '<video width="100" height="100" controls><source src="{}" type="video/mp4"></video>',
                obj.video_file.url
            )
        elif obj.external_url:
            return format_html('<a href="{}" target="_blank">Ver contenido</a>', obj.external_url)
        return 'Sin vista previa'
    
    media_preview.short_description = 'Vista previa'
    
    actions = ['make_public', 'make_private', 'mark_featured', 'unmark_featured']
    
    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} fichas marcadas como públicas.')
    make_public.short_description = "Marcar como públicas"
    
    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} fichas marcadas como privadas.')
    make_private.short_description = "Marcar como privadas"
    
    def mark_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} fichas marcadas como destacadas.')
    mark_featured.short_description = "Marcar como destacadas"
    
    def unmark_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} fichas desmarcadas como destacadas.')
    unmark_featured.short_description = "Desmarcar como destacadas"
