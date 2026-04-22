from django.contrib import admin
from django.utils.html import format_html
from .models import Video, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'category',
        'thumbnail_preview',
        'views',
        'is_public',
        'created_at'
    ]
    list_filter = ['category', 'is_public', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['views', 'created_at', 'updated_at', 'thumbnail_preview']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Video-Informationen', {
            'fields': ('title', 'description', 'category', 'uploaded_by')
        }),
        ('Dateien', {
            'fields': ('video_file', 'thumbnail', 'thumbnail_preview')
        }),
        ('Statistiken', {
            'fields': ('views', 'duration', 'is_public', 'created_at', 'updated_at')
        }),
    )
    
    def thumbnail_preview(self, obj):
        """Zeigt Thumbnail-Vorschau"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 150px;" />',
                obj.thumbnail.url
            )
        return '-'
    thumbnail_preview.short_description = 'Thumbnail-Vorschau'