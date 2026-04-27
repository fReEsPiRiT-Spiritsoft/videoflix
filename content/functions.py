from rest_framework.response import Response
from rest_framework import status
from authentication.authentication import CookieJWTAuthentication
from content.models import Video, VideoResolution
from django.http import HttpResponse, FileResponse
from django.conf import settings
import os


def check_video_authentication(request):
    """
    Prüft die JWT-Authentifizierung für Video-Endpoints.
    Gibt (user, error_response) zurück.
    """
    auth = CookieJWTAuthentication()
    try:
        user_auth = auth.authenticate(request)
        if user_auth is None:
            error_response = Response(
                {'error': 'Nicht authentifiziert.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            return None, error_response
        return user_auth[0], None
    except Exception:
        error_response = Response(
            {'error': 'Ungültiger Token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
        return None, error_response


def validate_video_resolution(resolution):
    """
    Validiert die Video-Auflösung.
    """
    valid_resolutions = ['480p', '720p', '1080p']
    return resolution in valid_resolutions


def validate_segment_filename(segment):
    """
    Validiert den Segment-Dateinamen gegen Path-Traversal.
    """
    if not segment.endswith('.ts'):
        return False
    if '..' in segment or '/' in segment or '\\' in segment:
        return False
    return True


def get_video_by_id(movie_id):
    """
    Holt ein Video aus der Datenbank.
    """
    try:
        return Video.objects.get(pk=movie_id, is_public=True, is_processed=True)
    except Video.DoesNotExist:
        return None


def get_video_resolution(video, resolution):
    """
    Holt eine VideoResolution für ein Video.
    """
    try:
        return VideoResolution.objects.get(video=video, resolution=resolution, is_ready=True)
    except VideoResolution.DoesNotExist:
        return None


def get_playlist_path(movie_id, resolution):
    """
    Generiert den Pfad zur HLS-Playlist.
    """
    return os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(movie_id), resolution, 'index.m3u8')


def get_segment_path(movie_id, resolution, segment):
    """
    Generiert den Pfad zu einem Video-Segment.
    """
    return os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(movie_id), resolution, segment)


def read_playlist_file(playlist_path):
    """
    Liest eine M3U8-Playlist-Datei.
    """
    try:
        with open(playlist_path, 'r') as f:
            return f.read()
    except Exception:
        return None


def create_segment_response(segment_path):
    """
    Erstellt eine FileResponse für ein Video-Segment.
    """
    response = FileResponse(open(segment_path, 'rb'), content_type='video/MP2T')
    response['Cache-Control'] = 'public, max-age=31536000'
    return response


def validate_and_get_video_resolution(movie_id, resolution):
    """
    Validiert Auflösung und gibt Video + VideoResolution zurück.
    Gibt (video, video_resolution, error_response) zurück.
    """
    if not validate_video_resolution(resolution):
        return None, None, Response({'error': 'Ungültige Auflösung.'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
    
    video = get_video_by_id(movie_id)
    if not video:
        return None, None, Response({'error': 'Video nicht gefunden.'}, 
                                   status=status.HTTP_404_NOT_FOUND)
    
    video_resolution = get_video_resolution(video, resolution)
    if not video_resolution:
        return None, None, Response({'error': f'Video nicht in {resolution} verfügbar.'}, 
                                   status=status.HTTP_404_NOT_FOUND)
    
    return video, video_resolution, None


def get_playlist_content(movie_id, resolution):
    """
    Liest den Playlist-Inhalt und gibt (content, error_response) zurück.
    """
    playlist_path = get_playlist_path(movie_id, resolution)
    if not os.path.exists(playlist_path):
        return None, Response({'error': 'Manifest nicht gefunden.'}, 
                             status=status.HTTP_404_NOT_FOUND)
    
    content = read_playlist_file(playlist_path)
    if not content:
        return None, Response({'error': 'Fehler beim Laden der Playlist.'}, 
                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return content, None
