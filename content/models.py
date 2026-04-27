"""Content models for video streaming platform.

This module contains the data models for video content management, including
categories, videos, and video resolutions for HLS streaming.
"""

from django.db import models
from django.contrib.auth.models import User
import os


class Category(models.Model):
    """Video category model for content organization.
    
    Represents content categories (e.g., Drama, Action, Romance) for
    organizing and filtering videos.
    """
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Video(models.Model):
    """Main video content model.
    
    Stores video metadata, file references, and processing status for
    HLS (HTTP Live Streaming) delivery.
    """
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_file = models.FileField(upload_to='videos/%Y/%m/')
    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='videos')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")
    views = models.IntegerField(default=0)
    is_public = models.BooleanField(default=True)
    is_processed = models.BooleanField(default=False, help_text="Indicates if video has been processed for HLS")
    
    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def thumbnail_url(self):
        """Get the thumbnail URL if available.
        
        Returns:
            str: Thumbnail URL or None.
        """
        if self.thumbnail:
            return self.thumbnail.url
        return None
    
    def get_hls_path(self, resolution):
        """Get the HLS playlist path for a specific resolution.
        
        Args:
            resolution: Video resolution string (e.g., '480p').
            
        Returns:
            str: Path to HLS playlist file (e.g., 'videos/hls/1/480p/index.m3u8').
        """
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