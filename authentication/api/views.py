from django.http import HttpResponse
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
from authentication.utils import send_password_reset_email
from .serializers import (
    RegistrationSerializer, 
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from urllib.parse import unquote

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
            'token': user.activation_token_value
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([AllowAny])
def activate_view(request, uidb64, token):
    """
    GET /api/auth/activate/<uidb64>/<token>/
    Aktiviert das Benutzerkonto und zeigt HTML-Bestätigung.
    """
    #token = unquote(token)
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Aktivierung fehlgeschlagen</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }
                .box { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .error { color: #dc3545; }
                h1 { color: #dc3545; }
            </style>
        </head>
        <body>
            <div class="box">
                <h1>❌ Aktivierung fehlgeschlagen</h1>
                <p class="error">Der Aktivierungslink ist ungültig.</p>
            </div>
        </body>
        </html>
        """, status=400)
    
    try:
        activation_token = ActivationToken.objects.get(user=user, token=token)
    except ActivationToken.DoesNotExist:
        return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Token ungültig</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }
                .box { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .error { color: #dc3545; }
                h1 { color: #dc3545; }
            </style>
        </head>
        <body>
            <div class="box">
                <h1>❌ Token ungültig</h1>
                <p class="error">Der Aktivierungstoken ist ungültig oder wurde bereits verwendet.</p>
            </div>
        </body>
        </html>
        """, status=400)
    
    if not activation_token.is_valid():
        activation_token.delete()
        return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Token abgelaufen</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }
                .box { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .error { color: #dc3545; }
                h1 { color: #dc3545; }
            </style>
        </head>
        <body>
            <div class="box">
                <h1>⏰ Token abgelaufen</h1>
                <p class="error">Der Aktivierungstoken ist abgelaufen (24h Gültigkeit).</p>
                <p>Bitte registriere dich erneut.</p>
            </div>
        </body>
        </html>
        """, status=400)
    
    # Aktiviere User
    if not user.is_active:
        user.is_active = True
        user.save()
        activation_token.delete()
        
        return HttpResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Account aktiviert</title>
            <style>
                body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }}
                .box {{ background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .success {{ color: #28a745; }}
                h1 {{ color: #28a745; }}
                a {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
                a:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <div class="box">
                <h1>✅ Account erfolgreich aktiviert!</h1>
                <p class="success">Dein Account <strong>{user.email}</strong> wurde aktiviert.</p>
                <p>Du kannst dich jetzt einloggen.</p>
                <a href="http://localhost:5500/login.html">Zum Login</a>
            </div>
        </body>
        </html>
        """, status=200)
    else:
        return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bereits aktiviert</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }
                .box { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .info { color: #007bff; }
                h1 { color: #007bff; }
                a { display: inline-block; margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                a:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="box">
                <h1>ℹ️ Account bereits aktiv</h1>
                <p class="info">Dieser Account ist bereits aktiviert.</p>
                <a href="http://localhost:5500/login.html">Zum Login</a>
            </div>
        </body>
        </html>
        """, status=400)
    
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
            
            # Sende E-Mail
            send_password_reset_email(user, reset_token.token)
            
        except User.DoesNotExist:
            pass  # Keine Fehlermeldung aus Sicherheitsgründen
        
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