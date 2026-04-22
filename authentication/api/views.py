from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from authentication.models import ActivationToken, PasswordResetToken
from .serializers import (
    RegistrationSerializer, 
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

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
        activation_token.delete()  
        
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
            secure=False,  
            samesite='Lax',
            max_age=3600  
        )
        
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=False, 
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
    refresh_token = request.COOKIES.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh-Token fehlt.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        response = Response(
            {'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'},
            status=status.HTTP_200_OK
        )
        
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        return response
        
    except TokenError as e:
        return Response(
            {'error': 'Ungültiger oder abgelaufener Token.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    POST /api/token/refresh/
    Gibt ein neues Zugangstoken aus, wenn der alte Access-Token abgelaufen ist.
    """
    refresh_token = request.COOKIES.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh-Token fehlt.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        response = Response(
            {
                'detail': 'Token refreshed',
                'access': access_token
            },
            status=status.HTTP_200_OK
        )
        
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=3600
        )
        
        return response
        
    except TokenError as e:
        return Response(
            {'error': 'Ungültiger Refresh-Token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """
    POST /api/password_reset/
    Sendet einen Link zum Zurücksetzen des Passworts an die E-Mail des Benutzers.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Erstelle Reset-Token
            reset_token = PasswordResetToken.objects.create(
                user=user,
                token=PasswordResetToken.generate_token()
            )
            
            # Kodiere User-ID für URL
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            
            # TODO: E-Mail mit Reset-Link versenden
            # reset_url = f"http://yourfrontend.com/password-reset/{uidb64}/{reset_token.token}/"
            # send_password_reset_email(user, reset_url)
            
            # Für Entwicklung: Token im Response (NICHT in Production!)
            print(f"Password Reset URL: /api/password_confirm/{uidb64}/{reset_token.token}/")
            
        except User.DoesNotExist:
            # Aus Sicherheitsgründen keine Fehlermeldung
            # (verhindert E-Mail-Enumeration)
            pass
        
        # Immer erfolgreiche Response, auch wenn E-Mail nicht existiert
        return Response(
            {'detail': 'An email has been sent to reset your password.'},
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request, uidb64, token):
    """
    POST /api/password_confirm/<uidb64>/<token>/
    Setzt das Passwort mit dem Token zurück.
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Dekodiere User-ID
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'error': 'Invalid password reset link.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validiere Token
    try:
        reset_token = PasswordResetToken.objects.get(user=user, token=token)
    except PasswordResetToken.DoesNotExist:
        return Response(
            {'error': 'Invalid or expired password reset token.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Prüfe Token-Gültigkeit
    if not reset_token.is_valid():
        reset_token.delete()
        return Response(
            {'error': 'Password reset token has expired.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Setze neues Passwort
    new_password = serializer.validated_data['password']
    user.set_password(new_password)
    user.save()
    
    # Markiere Token als verwendet und lösche
    reset_token.used = True
    reset_token.save()
    reset_token.delete()
    
    return Response(
        {'detail': 'Password has been reset successfully.'},
        status=status.HTTP_200_OK
    )