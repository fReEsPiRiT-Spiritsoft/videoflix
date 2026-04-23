from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import FileResponse, Http404, HttpResponse
from django.conf import settings
from authentication.authentication import CookieJWTAuthentication
from content.models import Video, VideoResolution
from .serializers import VideoListSerializer, VideoDetailSerializer
import os


@api_view(['GET'])
@authentication_classes([CookieJWTAuthentication]) 
@permission_classes([IsAuthenticated])
def video_list_view(request):
    """
    GET /api/video/
    Gibt eine Liste aller verfügbaren Videos zurück.
    """
    auth = CookieJWTAuthentication()
    try:
        user_auth = auth.authenticate(request)
        if user_auth is None:
            return Response(
                {'error': 'Nicht authentifiziert.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except Exception as e:
        return Response(
            {'error': 'Ungültiger Token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    videos = Video.objects.filter(is_public=True, is_processed=True).select_related('category')
    serializer = VideoListSerializer(videos, many=True, context={'request': request})
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_detail_view(request, pk):
    """
    GET /api/video/<id>/
    Gibt Details zu einem spezifischen Video zurück.
    """
    auth = CookieJWTAuthentication()
    try:
        user_auth = auth.authenticate(request)
        if user_auth is None:
            return Response(
                {'error': 'Nicht authentifiziert.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except Exception as e:
        return Response(
            {'error': 'Ungültiger Token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        video = Video.objects.select_related('category', 'uploaded_by').get(pk=pk, is_public=True)
    except Video.DoesNotExist:
        return Response(
            {'error': 'Video nicht gefunden.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    video.views += 1
    video.save(update_fields=['views'])
    
    serializer = VideoDetailSerializer(video, context={'request': request})
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_hls_playlist_view(request, movie_id, resolution):
    """
    GET /api/video/<movie_id>/<resolution>/index.m3u8
    Gibt die HLS-Master-Playlist für einen bestimmten Film und eine gewählte Auflösung zurück.
    """
    # Authentifizierung
    auth = CookieJWTAuthentication()
    try:
        user_auth = auth.authenticate(request)
        if user_auth is None:
            return Response(
                {'error': 'Nicht authentifiziert.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except Exception as e:
        return Response(
            {'error': 'Ungültiger Token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validiere Auflösung
    valid_resolutions = ['480p', '720p', '1080p']
    if resolution not in valid_resolutions:
        return Response(
            {'error': f'Ungültige Auflösung. Erlaubt: {", ".join(valid_resolutions)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Hole Video
    try:
        video = Video.objects.get(pk=movie_id, is_public=True, is_processed=True)
    except Video.DoesNotExist:
        return Response(
            {'error': 'Video nicht gefunden oder nicht verfügbar.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Hole VideoResolution
    try:
        video_resolution = VideoResolution.objects.get(
            video=video,
            resolution=resolution,
            is_ready=True
        )
    except VideoResolution.DoesNotExist:
        return Response(
            {'error': f'Video nicht in {resolution} verfügbar.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Pfad zur HLS-Playlist
    playlist_path = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(movie_id), resolution, 'index.m3u8')
    
    if not os.path.exists(playlist_path):
        return Response(
            {'error': 'Manifest nicht gefunden.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Lese und sende die .m3u8 Datei
    try:
        with open(playlist_path, 'r') as f:
            playlist_content = f.read()
        
        return HttpResponse(
            playlist_content,
            content_type='application/vnd.apple.mpegurl',
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': 'Fehler beim Laden der Playlist.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_hls_segment_view(request, movie_id, resolution, segment):
    """
    GET /api/video/<movie_id>/<resolution>/<segment>/
    Gibt ein einzelnes HLS-Videosegment für einen bestimmten Film in gewählter Auflösung zurück.
    """
    # Authentifizierung
    auth = CookieJWTAuthentication()
    try:
        user_auth = auth.authenticate(request)
        if user_auth is None:
            return Response(
                {'error': 'Nicht authentifiziert.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except Exception as e:
        return Response(
            {'error': 'Ungültiger Token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validiere Auflösung
    valid_resolutions = ['480p', '720p', '1080p']
    if resolution not in valid_resolutions:
        return Response(
            {'error': f'Ungültige Auflösung. Erlaubt: {", ".join(valid_resolutions)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validiere Segment-Dateiname (Sicherheit: nur .ts Dateien erlauben)
    if not segment.endswith('.ts'):
        return Response(
            {'error': 'Ungültiges Segment-Format. Nur .ts-Dateien erlaubt.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verhindere Path-Traversal-Attacken
    if '..' in segment or '/' in segment or '\\' in segment:
        return Response(
            {'error': 'Ungültiger Segment-Name.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Hole Video
    try:
        video = Video.objects.get(pk=movie_id, is_public=True, is_processed=True)
    except Video.DoesNotExist:
        return Response(
            {'error': 'Video nicht gefunden oder nicht verfügbar.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Hole VideoResolution
    try:
        video_resolution = VideoResolution.objects.get(
            video=video,
            resolution=resolution,
            is_ready=True
        )
    except VideoResolution.DoesNotExist:
        return Response(
            {'error': f'Video nicht in {resolution} verfügbar.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Pfad zum Segment
    segment_path = os.path.join(
        settings.MEDIA_ROOT, 
        'videos', 
        'hls', 
        str(movie_id), 
        resolution, 
        segment
    )
    
    # Prüfe ob Datei existiert
    if not os.path.exists(segment_path):
        return Response(
            {'error': 'Video oder Segment nicht gefunden.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Sende Segment als binäre Datei
    try:
        response = FileResponse(
            open(segment_path, 'rb'),
            content_type='video/MP2T'  # MPEG-2 Transport Stream
        )
        
        # Optional: Cache-Header für bessere Performance
        response['Cache-Control'] = 'public, max-age=31536000'  # 1 Jahr
        
        return response
        
    except Exception as e:
        return Response(
            {'error': 'Fehler beim Laden des Segments.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )