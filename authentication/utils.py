"""Utility functions for authentication email operations.

This module provides helper functions for building activation and password
reset links, and sending corresponding email notifications to users.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string


def build_activation_link(user, token):
    """Build the account activation link for email.
    
    Args:
        user: User object to activate.
        token: Activation token string.
        
    Returns:
        str: Complete activation URL.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    return f"http://localhost:8000/api/activate/{uidb64}/{token}/"


def send_activation_email(user, token):
    """Send account activation email with HTML and text templates.
    
    Args:
        user: User object receiving the activation email.
        token: Activation token string.
        
    Returns:
        bool: True if email was sent successfully, False otherwise.
    """
    activation_link = build_activation_link(user, token)
    context = {'user_email': user.email, 'activation_link': activation_link}
    
    html_message = render_to_string(
        'authentication/emails/activation_email.html',
        context
    )
    text_message = render_to_string(
        'authentication/emails/activation_email.txt',
        context
    )
    
    try:
        send_mail(
            subject='Activate your Videoflix Account',
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


def build_password_reset_link(user, token):
    """Build the password reset link for email.
    
    Args:
        user: User object requesting password reset.
        token: Password reset token string.
        
    Returns:
        str: Complete password reset URL.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    return f"http://localhost:8000/api/password-reset/{uidb64}/{token}/"


def send_password_reset_email(user, token):
    """Send password reset email with HTML and text templates.
    
    Args:
        user: User object receiving the password reset email.
        token: Password reset token string.
        
    Returns:
        bool: True if email was sent successfully, False otherwise.
    """
    reset_link = build_password_reset_link(user, token)
    context = {'user_email': user.email, 'reset_link': reset_link}
    
    html_message = render_to_string(
        'authentication/emails/password_reset_email.html',
        context
    )
    text_message = render_to_string(
        'authentication/emails/password_reset_email.txt',
        context
    )
    
    try:
        send_mail(
            subject='Reset Your Password - Videoflix',
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False