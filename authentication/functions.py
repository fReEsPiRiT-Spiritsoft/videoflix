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
    """
    Rendert eine HTML-Aktivierungs-Response.
    """
    html = render_to_string(f'authentication/{template_name}', context or {})
    return HttpResponse(html, status=status_code)


def get_user_from_uidb64(uidb64):
    """
    Dekodiert uidb64 und gibt den User zurück.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def get_activation_token(user, token):
    """
    Holt und validiert den Aktivierungstoken.
    """
    try:
        return ActivationToken.objects.get(user=user, token=token)
    except ActivationToken.DoesNotExist:
        return None


def get_password_reset_token(user, token):
    """
    Holt und validiert den Password-Reset-Token.
    """
    try:
        return PasswordResetToken.objects.get(user=user, token=token)
    except PasswordResetToken.DoesNotExist:
        return None


def activate_user_account(user, activation_token):
    """
    Aktiviert den User-Account und löscht den Token.
    """
    if not user.is_active:
        user.is_active = True
        user.save()
        activation_token.delete()
        return True
    return False


def create_jwt_tokens(user):
    """
    Erstellt JWT Access- und Refresh-Tokens für einen User.
    """
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_jwt_cookies(response, access_token, refresh_token):
    """
    Setzt JWT-Tokens als HttpOnly-Cookies.
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
    """
    Setzt den Refresh-Token auf die Blacklist.
    """
    try:
        token = RefreshToken(refresh_token_string)
        token.blacklist()
        return True
    except TokenError:
        return False


def refresh_access_token(refresh_token_string):
    """
    Erstellt ein neues Access-Token aus einem Refresh-Token.
    """
    try:
        refresh = RefreshToken(refresh_token_string)
        return str(refresh.access_token)
    except TokenError:
        return None


def reset_user_password(user, new_password, reset_token):
    """
    Setzt das User-Passwort zurück und löscht den Token.
    """
    user.set_password(new_password)
    user.save()
    reset_token.used = True
    reset_token.save()
    reset_token.delete()


def create_password_reset_token(user):
    """
    Erstellt einen neuen Password-Reset-Token.
    """
    from authentication.utils import send_password_reset_email
    reset_token = PasswordResetToken.objects.create(
        user=user,
        token=PasswordResetToken.generate_token()
    )
    send_password_reset_email(user, reset_token.token)
    return reset_token
