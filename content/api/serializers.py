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
        """Get absolute thumbnail URL.
        
        Args:
            obj: Video instance.
            
        Returns:
            str: Absolute thumbnail URL or None.
        """
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None


class VideoDetailSerializer(serializers.ModelSerializer):
    """Serializer for video detail view.
    
    Provides complete video information including category details,
    uploader info, and available resolutions for streaming.
    """
    
    thumbnail_url = serializers.SerializerMethodField()
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
        """Get absolute thumbnail URL.
        
        Args:
            obj: Video instance.
            
        Returns:
            str: Absolute thumbnail URL or None.
        """
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None