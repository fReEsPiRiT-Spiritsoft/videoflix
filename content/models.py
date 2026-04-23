from django.db import models
from django.contrib.auth.models import User
import os


class Category(models.Model):
    """Kategorien für Videos (z.B. Drama, Action, Romance)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = "Kategorie"
        verbose_name_plural = "Kategorien"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Video(models.Model):
    """Hauptmodel für Videos"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_file = models.FileField(upload_to='videos/%Y/%m/')
    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='videos')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Video-Informationen
    duration = models.IntegerField(null=True, blank=True, help_text="Dauer in Sekunden")
    views = models.IntegerField(default=0)
    is_public = models.BooleanField(default=True)
    
    # HLS-Processing Status
    is_processed = models.BooleanField(default=False, help_text="Gibt an, ob Video für HLS verarbeitet wurde")
    
    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def thumbnail_url(self):
        """Gibt die URL des Thumbnails zurück"""
        if self.thumbnail:
            return self.thumbnail.url
        return None
    
    def get_hls_path(self, resolution):
        """Gibt den Pfad zur HLS-Playlist für eine bestimmte Auflösung zurück"""
        # Beispiel: media/videos/hls/1/480p/index.m3u8
        return os.path.join('videos', 'hls', str(self.id), resolution, 'index.m3u8')


class VideoResolution(models.Model):
    """Speichert verschiedene Auflösungen eines Videos"""
    RESOLUTION_CHOICES = [
        ('480p', '480p'),
        ('720p', '720p'),
        ('1080p', '1080p'),
    ]
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='resolutions')
    resolution = models.CharField(max_length=10, choices=RESOLUTION_CHOICES)
    hls_playlist = models.FileField(upload_to='videos/hls/', blank=True, null=True)
    file_size = models.BigIntegerField(default=0, help_text="Dateigröße in Bytes")
    is_ready = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Video-Auflösung"
        verbose_name_plural = "Video-Auflösungen"
        unique_together = ['video', 'resolution']
    
    def __str__(self):
        return f"{self.video.title} - {self.resolution}"