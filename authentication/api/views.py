"""API views for user authentication and account management.

This module provides RESTful API endpoints for user registration, account
activation, login, logout, token refresh, and password reset functionality.
"""

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
from authentication.functions import (
    render_activation_response,
    get_user_from_uidb64,
    get_activation_token,
    get_password_reset_token,
    activate_user_account,
    create_jwt_tokens,
    set_jwt_cookies,
    blacklist_refresh_token,
    refresh_access_token,
    reset_user_password,
    create_password_reset_token
)
from .serializers import (
    RegistrationSerializer, 
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Register a new user in the system.
    
    Creates an inactive user account and sends activation email with token.
    
    Args:
        request: HTTP request containing user registration data.
        
    Returns:
        Response: 201 with user data and token on success, 400 on validation error.
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
    """Activate a user account via email verification link.
    
    Validates the activation token and activates the user account if valid.
    
    Args:
        request: HTTP request object.
        uidb64: Base64-encoded user ID.
        token: Activation token string.
        
    Returns:
        HttpResponse: Rendered HTML page showing activation result.
    """
    user = get_user_from_uidb64(uidb64)
    if not user:
        return render_activation_response('activation_invalid_link.html', status_code=400)
    
    activation_token = get_activation_token(user, token)
    if not activation_token:
        return render_activation_response('activation_token_invalid.html', status_code=400)
    
    if not activation_token.is_valid():
        activation_token.delete()
        return render_activation_response('activation_token_expired.html', status_code=400)
    
    if activate_user_account(user, activation_token):
        context = {'user_email': user.email}
        return render_activation_response('activation_success.html', context)
    
    return render_activation_response('activation_already_active.html', status_code=400)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticate a user and issue JWT tokens.
    
    Validates credentials and sets JWT tokens as HTTP-only cookies.
    
    Args:
        request: HTTP request containing login credentials.
        
    Returns:
        Response: 200 with user data and tokens on success, 400 on error.
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = serializer.validated_data['user']
    access_token, refresh_token = create_jwt_tokens(user)
    
    response = Response({
        'detail': 'Login successful',
        'user': {'id': user.id, 'username': user.email}
    }, status=status.HTTP_200_OK)
    
    set_jwt_cookies(response, access_token, refresh_token)
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """Log out a user and invalidate refresh token.
    
    Blacklists the refresh token and clears authentication cookies.
    
    Args:
        request: HTTP request containing refresh token in cookies.
        
    Returns:
        Response: 200 on successful logout, 400 if token missing or invalid.
    """
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return Response({'error': 'Refresh token missing.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if not blacklist_refresh_token(refresh_token):
        return Response({'error': 'Invalid or expired token.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    response = Response({'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'}, 
                       status=status.HTTP_200_OK)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """Refresh access token using refresh token.
    
    Generates a new access token from a valid refresh token.
    
    Args:
        request: HTTP request containing refresh token in cookies.
        
    Returns:
        Response: 200 with new access token on success, 400/401 on error.
    """
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return Response({'error': 'Refresh token missing.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    access_token = refresh_access_token(refresh_token)
    if not access_token:
        return Response({'error': 'Invalid refresh token.'}, 
                       status=status.HTTP_401_UNAUTHORIZED)
    
    response = Response({'detail': 'Token refreshed', 'access': access_token}, 
                       status=status.HTTP_200_OK)
    response.set_cookie(key='access_token', value=access_token, httponly=True, 
                       secure=False, samesite='Lax', max_age=3600)
    return response
    


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """Request a password reset email.
    
    Sends password reset email if account exists and is active.
    
    Args:
        request: HTTP request containing email address.
        
    Returns:
        Response: 200 with success message (always, for security).
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=serializer.validated_data['email'], is_active=True)
        create_password_reset_token(user)
    except User.DoesNotExist:
        pass
    
    return Response({'detail': 'An email has been sent to reset your password.'}, 
                   status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request, uidb64, token):
    """Confirm password reset and set new password.
    
    Validates reset token and updates user password if valid.
    
    Args:
        request: HTTP request containing new password.
        uidb64: Base64-encoded user ID.
        token: Password reset token string.
        
    Returns:
        Response: 200 on success, 400 on validation error or invalid token.
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = get_user_from_uidb64(uidb64)
    if not user:
        return Response({'error': 'Invalid password reset link.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    reset_token = get_password_reset_token(user, token)
    if not reset_token or not reset_token.is_valid():
        if reset_token:
            reset_token.delete()
        return Response({'error': 'Invalid or expired password reset token.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    reset_user_password(user, serializer.validated_data['password'], reset_token)
    return Response({'detail': 'Password has been reset successfully.'}, 
                   status=status.HTTP_200_OK)