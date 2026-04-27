from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string


def build_activation_link(user, token):
    """
    Erstellt den Aktivierungslink.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    return f"http://localhost:8000/api/activate/{uidb64}/{token}/"


def send_activation_email(user, token):
    """
    Sendet Aktivierungs-Email mit Template.
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
            subject='Aktiviere deinen Videoflix-Account',
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"E-Mail-Versand fehlgeschlagen: {e}")
        return False


def build_password_reset_link(user, token):
    """
    Erstellt den Passwort-Reset-Link.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    return f"http://localhost:8000/api/password-reset/{uidb64}/{token}/"


def send_password_reset_email(user, token):
    """
    Sendet Passwort-Zurücksetzen-Email mit Template.
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
            subject='Passwort zurücksetzen - Videoflix',
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"E-Mail-Versand fehlgeschlagen: {e}")
        return False