"""Helper functions for authentication operations.

This module contains utility functions for handling user authentication flows,
including activation responses, token management, JWT operations, and password
reset functionality.
"""

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from authentication.models import ActivationToken, PasswordResetToken
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


def render_activation_response(template_name, context=None, status_code=200):
    """Render an HTML activation response template.
    
    Args:
        template_name: Name of the template file to render.
        context: Dictionary of context variables for template.
        status_code: HTTP status code for the response.
        
    Returns:
        HttpResponse: Rendered HTML response.
    """
    html = render_to_string(f'authentication/{template_name}', context or {})
    return HttpResponse(html, status=status_code)


def get_user_from_uidb64(uidb64):
    """Decode base64-encoded user ID and retrieve User object.
    
    Args:
        uidb64: Base64-encoded user ID string.
        
    Returns:
        User: User object if found and valid, None otherwise.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def get_activation_token(user, token):
    """Retrieve and validate activation token for a user.
    
    Args:
        user: User object to check activation token for.
        token: Activation token string to validate.
        
    Returns:
        ActivationToken: Token object if found, None otherwise.
    """
    try:
        return ActivationToken.objects.get(user=user, token=token)
    except ActivationToken.DoesNotExist:
        return None


def get_password_reset_token(user, token):
    """Retrieve and validate password reset token for a user.
    
    Args:
        user: User object to check password reset token for.
        token: Password reset token string to validate.
        
    Returns:
        PasswordResetToken: Token object if found, None otherwise.
    """
    try:
        return PasswordResetToken.objects.get(user=user, token=token)
    except PasswordResetToken.DoesNotExist:
        return None


def activate_user_account(user, activation_token):
    """Activate a user account and delete the activation token.
    
    Args:
        user: User object to activate.
        activation_token: ActivationToken object to consume.
        
    Returns:
        bool: True if account was activated, False if already active.
    """
    if not user.is_active:
        user.is_active = True
        user.save()
        activation_token.delete()
        return True
    return False


def create_jwt_tokens(user):
    """Create JWT access and refresh tokens for a user.
    
    Args:
        user: User object to create tokens for.
        
    Returns:
        tuple: (access_token, refresh_token) as strings.
    """
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_jwt_cookies(response, access_token, refresh_token):
    """Set JWT tokens as HTTP-only cookies on response.
    
    Args:
        response: Response object to set cookies on.
        access_token: JWT access token string.
        refresh_token: JWT refresh token string.
    """
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


def blacklist_refresh_token(refresh_token_string):
    """Add a refresh token to the blacklist to invalidate it.
    
    Args:
        refresh_token_string: Refresh token string to blacklist.
        
    Returns:
        bool: True if blacklisting succeeded, False otherwise.
    """
    try:
        token = RefreshToken(refresh_token_string)
        token.blacklist()
        return True
    except TokenError:
        return False


def refresh_access_token(refresh_token_string):
    """Generate a new access token from a refresh token.
    
    Args:
        refresh_token_string: Valid refresh token string.
        
    Returns:
        str: New access token if successful, None otherwise.
    """
    try:
        refresh = RefreshToken(refresh_token_string)
        return str(refresh.access_token)
    except TokenError:
        return None


def reset_user_password(user, new_password, reset_token):
    """Reset user password and mark token as used.
    
    Args:
        user: User object to reset password for.
        new_password: New password string to set.
        reset_token: PasswordResetToken object to consume.
    """
    user.set_password(new_password)
    user.save()
    reset_token.used = True
    reset_token.save()
    reset_token.delete()


def create_password_reset_token(user):
    """Create a new password reset token and send email.
    
    Args:
        user: User object to create reset token for.
        
    Returns:
        PasswordResetToken: Created token object.
    """
    from authentication.utils import send_password_reset_email
    reset_token = PasswordResetToken.objects.create(
        user=user,
        token=PasswordResetToken.generate_token()
    )
    send_password_reset_email(user, reset_token.token)
    return reset_token
