from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from authentication.authentication import CookieJWTAuthentication
from content.models import Video
from .serializers import VideoListSerializer, VideoDetailSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_list_view(request):
    """
    GET /api/video/
    Gibt eine Liste aller verfügbaren Videos zurück.
    """
    # Authentifizierung über Custom CookieJWTAuthentication
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
    
    # Hole alle öffentlichen Videos
    videos = Video.objects.filter(is_public=True).select_related('category')
    
    # Serialisiere Videos
    serializer = VideoListSerializer(videos, many=True, context={'request': request})
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_detail_view(request, pk):
    """
    GET /api/video/<id>/
    Gibt Details zu einem spezifischen Video zurück.
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
    
    try:
        video = Video.objects.select_related('category', 'uploaded_by').get(pk=pk, is_public=True)
    except Video.DoesNotExist:
        return Response(
            {'error': 'Video nicht gefunden.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Erhöhe View-Counter
    video.views += 1
    video.save(update_fields=['views'])
    
    # Serialisiere Video
    serializer = VideoDetailSerializer(video, context={'request': request})
    
    return Response(serializer.data, status=status.HTTP_200_OK)