"""Serializers for content API endpoints.

This module provides DRF serializers for video and category models,
including list and detail views with related data.
"""

from rest_framework import serializers
from content.models import Video, Category, VideoResolution


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for video categories."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class VideoResolutionSerializer(serializers.ModelSerializer):
    """Serializer for available video resolutions."""
    
    class Meta:
        model = VideoResolution
        fields = ['resolution', 'is_ready', 'file_size']


class VideoListSerializer(serializers.ModelSerializer):
    """Serializer for video list view.
    
    Provides basic video information for list endpoints with
    thumbnail URLs and category names.
    """
    
    thumbnail_url = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id',
            'created_at',
            'title',
            'description',
            'thumbnail_url',
            'category'
        ]
    
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail:
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        if request:
            return request.build_absolute_uri('/static/images/thumbnail_placeholder.jpg')
        return '/static/images/thumbnail_placeholder.jpg'


class VideoDetailSerializer(serializers.ModelSerializer):
    """Serializer for video detail view.
    
    Provides complete video information including category details,
    uploader info, and available resolutions for streaming.
    """
    
    thumbnail_url = serializers.SerializerMethodField()
    master_playlist_url = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    uploaded_by = serializers.CharField(source='uploaded_by.username', read_only=True)
    available_resolutions = VideoResolutionSerializer(source='resolutions', many=True, read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'description',
            'video_file',
            'thumbnail_url',
            'master_playlist_url',
            'category',
            'uploaded_by',
            'created_at',
            'updated_at',
            'duration',
            'views',
            'is_processed',
            'available_resolutions'
        ]
    
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail:
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        if request:
            return request.build_absolute_uri('/static/images/thumbnail_placeholder.jpg')
        return '/static/images/thumbnail_placeholder.jpg'
    
    def get_master_playlist_url(self, obj):
        """Get absolute URL to HLS master playlist for adaptive streaming.
        
        Args:
            obj: Video instance.
            
        Returns:
            str: Absolute URL to master.m3u8 or None if not processed.
        """
        if not obj.is_processed:
            return None
        
        request = self.context.get('request')
        if request:
            from django.urls import reverse
            path = reverse('content_api:video_hls_master_playlist', kwargs={'movie_id': obj.id})
            return request.build_absolute_uri(path)
        return None