"""API views for video content endpoints.

This module provides RESTful API endpoints for video listing, details,
and HLS streaming (playlists and segments).
"""

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import FileResponse, Http404, HttpResponse
from django.conf import settings
from authentication.authentication import CookieJWTAuthentication
from content.models import Video, VideoResolution
from content.functions import (
    check_video_authentication,
    validate_video_resolution,
    validate_segment_filename,
    get_video_by_id,
    get_video_resolution,
    get_playlist_path,
    get_segment_path,
    read_playlist_file,
    create_segment_response,
    validate_and_get_video_resolution,
    get_playlist_content
)
from .serializers import VideoListSerializer, VideoDetailSerializer
import os


@api_view(['GET'])
@authentication_classes([CookieJWTAuthentication]) 
@permission_classes([IsAuthenticated])
def video_list_view(request):
    """Get list of all available videos.
    
    Returns a list of public, processed videos with basic information.
    
    Args:
        request: HTTP request with authentication.
        
    Returns:
        Response: 200 with video list, 401 if not authenticated.
    """
    user, error_response = check_video_authentication(request)
    if error_response:
        return error_response
    
    videos = Video.objects.filter(is_public=True, is_processed=True).select_related('category')
    serializer = VideoListSerializer(videos, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_detail_view(request, pk):
    """Get detailed information about a specific video.
    
    Increments view count and returns full video details including
    available resolutions.
    
    Args:
        request: HTTP request with authentication.
        pk: Video primary key.
        
    Returns:
        Response: 200 with video details, 404 if not found.
    """
    user, error_response = check_video_authentication(request)
    if error_response:
        return error_response
    
    try:
        video = Video.objects.select_related('category', 'uploaded_by').get(pk=pk, is_public=True)
    except Video.DoesNotExist:
        return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    video.views += 1
    video.save(update_fields=['views'])
    serializer = VideoDetailSerializer(video, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_hls_playlist_view(request, movie_id, resolution):
    """Serve HLS playlist for a specific video and resolution.
    
    Returns the M3U8 playlist file for adaptive streaming.
    
    Args:
        request: HTTP request with authentication.
        movie_id: Video ID.
        resolution: Desired resolution (480p/720p/1080p).
        
    Returns:
        HttpResponse: M3U8 playlist content.
    """
    user, error_response = check_video_authentication(request)
    if error_response:
        return error_response
    
    video, video_resolution, error_response = validate_and_get_video_resolution(movie_id, resolution)
    if error_response:
        return error_response
    
    playlist_content, error_response = get_playlist_content(movie_id, resolution)
    if error_response:
        return error_response
    
    return HttpResponse(playlist_content, content_type='application/vnd.apple.mpegurl')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_hls_segment_view(request, movie_id, resolution, segment):
    """Serve HLS video segment.
    
    Returns individual transport stream segments for HLS playback.
    
    Args:
        request: HTTP request with authentication.
        movie_id: Video ID.
        resolution: Video resolution.
        segment: Segment filename.
        
    Returns:
        FileResponse: Video segment with caching headers.
    """
    user, error_response = check_video_authentication(request)
    if error_response:
        return error_response
    
    if not validate_segment_filename(segment):
        return Response({'error': 'Invalid segment name.'}, status=status.HTTP_400_BAD_REQUEST)
    
    video, video_resolution, error_response = validate_and_get_video_resolution(movie_id, resolution)
    if error_response:
        return error_response
    
    segment_path = get_segment_path(movie_id, resolution, segment)
    if not os.path.exists(segment_path):
        return Response({'error': 'Segment not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        return create_segment_response(segment_path)
    except Exception:
        return Response({'error': 'Error loading segment.'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)