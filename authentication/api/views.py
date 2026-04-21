from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from authentication.models import ActivationToken
from .serializers import RegistrationSerializer, LoginSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    POST /api/register/
    Registriert einen neuen Benutzer im System.
    """
    serializer = RegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email
            },
            'token': user.activation_token
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([AllowAny])
def activate_view(request, uidb64, token):
    """
    GET /api/activate/<uidb64>/<token>/
    Aktiviert das Benutzerkonto mithilfe des per E-Mail gesendeten Tokens.
    """
    try:
        # Dekodiere User-ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'error': 'Invalid activation link.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        activation_token = ActivationToken.objects.get(user=user, token=token)
    except ActivationToken.DoesNotExist:
        return Response(
            {'error': 'Invalid or expired activation token.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Prüfe Token-Gültigkeit
    if not activation_token.is_valid():
        activation_token.delete()
        return Response(
            {'error': 'Activation token has expired.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Aktiviere User
    if not user.is_active:
        user.is_active = True
        user.save()
        activation_token.delete()  # Token nach Verwendung löschen
        
        return Response(
            {'message': 'Account successfully activated.'},
            status=status.HTTP_200_OK
        )
    else:
        return Response(
            {'error': 'Account is already active.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    POST /api/login/
    Authentifiziert den Benutzer und gibt JWT-Tokens zurück.
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        response = Response({
            'detail': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.email 
            }
        }, status=status.HTTP_200_OK)
        
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,  # In Production auf True setzen (HTTPS)
            samesite='Lax',
            max_age=3600  
        )
        
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=False,  # In Production auf True setzen (HTTPS)
            samesite='Lax',
            max_age=604800  
        )
        
        return response
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """
    POST /api/logout/
    Meldet den Benutzer ab, indem der Refresh-Token ungültig gemacht wird.
    """
    # Hole Refresh-Token aus Cookie
    refresh_token = request.COOKIES.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh-Token fehlt.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Setze Token auf Blacklist
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        # Erstelle Response
        response = Response(
            {'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'},
            status=status.HTTP_200_OK
        )
        
        # Lösche beide Cookies
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        return response
        
    except TokenError as e:
        return Response(
            {'error': 'Ungültiger oder abgelaufener Token.'},
            status=status.HTTP_400_BAD_REQUEST
        )