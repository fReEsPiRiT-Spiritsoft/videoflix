from django.contrib import admin
from django.utils.html import format_html
from .models import Video, Category, VideoResolution


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


class VideoResolutionInline(admin.TabularInline):
    model = VideoResolution
    extra = 0
    readonly_fields = ['file_size', 'created_at']


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'category',
        'thumbnail_preview',
        'is_processed',
        'views',
        'is_public',
        'created_at'
    ]
    list_filter = ['category', 'is_public', 'is_processed', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['views', 'created_at', 'updated_at', 'thumbnail_preview']
    ordering = ['-created_at']
    inlines = [VideoResolutionInline]
    
    fieldsets = (
        ('Video-Informationen', {
            'fields': ('title', 'description', 'category', 'uploaded_by')
        }),
        ('Dateien', {
            'fields': ('video_file', 'thumbnail', 'thumbnail_preview')
        }),
        ('Statistiken', {
            'fields': ('views', 'duration', 'is_public', 'is_processed', 'created_at', 'updated_at')
        }),
    )
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 150px;" />',
                obj.thumbnail.url
            )
        return '-'
    thumbnail_preview.short_description = 'Thumbnail-Vorschau'


@admin.register(VideoResolution)
class VideoResolutionAdmin(admin.ModelAdmin):
    list_display = ['video', 'resolution', 'is_ready', 'file_size_mb', 'created_at']
    list_filter = ['resolution', 'is_ready', 'created_at']
    search_fields = ['video__title']
    readonly_fields = ['created_at']
    
    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "0 MB"
    file_size_mb.short_description = 'Dateigröße'