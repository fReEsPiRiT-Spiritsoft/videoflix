from rest_framework import serializers
from content.models import Video, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class VideoListSerializer(serializers.ModelSerializer):
    """Serializer für Video-Liste"""
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
        """Gibt die vollständige URL des Thumbnails zurück"""
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None


class VideoDetailSerializer(serializers.ModelSerializer):
    """Serializer für Video-Details"""
    thumbnail_url = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    uploaded_by = serializers.CharField(source='uploaded_by.username', read_only=True)
    
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
            'views'
        ]
    
    def get_thumbnail_url(self, obj):
        """Gibt die vollständige URL des Thumbnails zurück"""
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None