"""Helper functions for video content operations.

This module contains utility functions for video authentication, validation,
file operations, and HLS streaming support.
"""

import os

from django.conf import settings
from django.http import FileResponse

from rest_framework import status
from rest_framework.response import Response

from authentication.authentication import CookieJWTAuthentication
from content.models import Video, VideoResolution


def check_video_authentication(request):
    """Check JWT authentication for video endpoints.
    
    Args:
        request: HTTP request object.
        
    Returns:
        tuple: (user, None) if authenticated, (None, error_response) otherwise.
    """
    auth = CookieJWTAuthentication()
    try:
        user_auth = auth.authenticate(request)
        if user_auth is None:
            error_response = Response(
                {'error': 'Not authenticated.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            return None, error_response
        return user_auth[0], None
    except Exception:
        error_response = Response(
            {'error': 'Invalid token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
        return None, error_response


def validate_video_resolution(resolution):
    """Validate video resolution format.
    
    Args:
        resolution: Resolution string to validate.
        
    Returns:
        bool: True if resolution is valid (480p/720p/1080p).
    """
    valid_resolutions = ['480p', '720p', '1080p']
    return resolution in valid_resolutions


def validate_segment_filename(segment):
    """Validate segment filename to prevent path traversal attacks.
    
    Args:
        segment: Segment filename to validate.
        
    Returns:
        bool: True if filename is safe.
    """
    if not segment.endswith('.ts'):
        return False
    if '..' in segment or '/' in segment or '\\' in segment:
        return False
    return True


def get_video_by_id(movie_id):
    """Retrieve a video from database by ID.
    
    Args:
        movie_id: Video ID to retrieve.
        
    Returns:
        Video: Video object if found and public/processed, None otherwise.
    """
    try:
        return Video.objects.get(pk=movie_id, is_public=True, is_processed=True)
    except Video.DoesNotExist:
        return None


def get_video_resolution(video, resolution):
    """Get a VideoResolution for a video.
    
    Args:
        video: Video instance.
        resolution: Resolution string (e.g., '720p').
        
    Returns:
        VideoResolution: Resolution object if available, None otherwise.
    """
    try:
        return VideoResolution.objects.get(video=video, resolution=resolution, is_ready=True)
    except VideoResolution.DoesNotExist:
        return None


def get_master_playlist_path(movie_id):
    """Generate path to HLS master playlist file.
    
    Args:
        movie_id: Video ID.
        
    Returns:
        str: Absolute path to master playlist file.
    """
    return os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(movie_id), 'master.m3u8')


def get_playlist_path(movie_id, resolution):
    """Generate path to HLS playlist file.
    
    Args:
        movie_id: Video ID.
        resolution: Resolution string.
        
    Returns:
        str: Absolute path to playlist file.
    """
    return os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(movie_id), resolution, 'index.m3u8')


def get_segment_path(movie_id, resolution, segment):
    """Generate path to video segment file.
    
    Args:
        movie_id: Video ID.
        resolution: Resolution string.
        segment: Segment filename.
        
    Returns:
        str: Absolute path to segment file.
    """
    return os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(movie_id), resolution, segment)


def read_playlist_file(playlist_path):
    """Read M3U8 playlist file contents.
    
    Args:
        playlist_path: Path to playlist file.
        
    Returns:
        str: Playlist contents or None on error.
    """
    try:
        with open(playlist_path, 'r') as f:
            return f.read()
    except Exception:
        return None


def create_segment_response(segment_path):
    """Create FileResponse for a video segment.
    
    Args:
        segment_path: Path to segment file.
        
    Returns:
        FileResponse: Response with video segment and caching headers.
    """
    response = FileResponse(open(segment_path, 'rb'), content_type='video/MP2T')
    response['Cache-Control'] = 'public, max-age=31536000'
    return response


def validate_and_get_video_resolution(movie_id, resolution):
    """Validate resolution and retrieve video with resolution data.
    
    Combines validation and database lookups for video streaming endpoints.
    
    Args:
        movie_id: Video ID.
        resolution: Resolution string.
        
    Returns:
        tuple: (video, video_resolution, None) on success,
               (None, None, error_response) on error.
    """
    if not validate_video_resolution(resolution):
        return None, None, Response({'error': 'Invalid resolution.'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
    
    video = get_video_by_id(movie_id)
    if not video:
        return None, None, Response({'error': 'Video not found.'}, 
                                   status=status.HTTP_404_NOT_FOUND)
    
    video_resolution = get_video_resolution(video, resolution)
    if not video_resolution:
        return None, None, Response({'error': f'Video not available in {resolution}.'}, 
                                   status=status.HTTP_404_NOT_FOUND)
    
    return video, video_resolution, None


def get_playlist_content(movie_id, resolution):
    """Read playlist content and return with error handling.
    
    Args:
        movie_id: Video ID.
        resolution: Resolution string.
        
    Returns:
        tuple: (content, None) on success, (None, error_response) on error.
    """
    playlist_path = get_playlist_path(movie_id, resolution)
    if not os.path.exists(playlist_path):
        return None, Response({'error': 'Manifest not found.'}, 
                             status=status.HTTP_404_NOT_FOUND)
    
    content = read_playlist_file(playlist_path)
    if not content:
        return None, Response({'error': 'Error loading playlist.'}, 
                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return content, None
