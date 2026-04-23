from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string



def send_activation_email(user, token):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    activation_link = f"http://localhost:8000/api/activate/{uidb64}/{token}/"
    
    subject = 'Aktiviere deinen Videoflix-Account'
    
    # HTML Version
    html_message = f"""
    <html>
    <body>
        <h2>Hallo {user.email},</h2>
        <p>vielen Dank für deine Registrierung bei Videoflix!</p>
        <p>Bitte aktiviere deinen Account:</p>
        <p><a href="{activation_link}" style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">Account aktivieren</a></p>
        <p>Der Link ist 24 Stunden gültig.</p>
        <p>Falls du dich nicht registriert hast, ignoriere diese E-Mail.</p>
        <p>Viele Grüße<br>Dein Videoflix-Team</p>
    </body>
    </html>
    """
    
    # Plaintext Fallback
    message = f"Aktiviere deinen Account: {activation_link}"
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,  # HTML Version!
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"E-Mail-Versand fehlgeschlagen: {e}")
        return False


def send_password_reset_email(user, token):
    """
    Sendet Passwort-Zurücksetzen-E-Mail
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    reset_link = f"http://localhost:8000/api/password-reset/{uidb64}/{token}/"
    
    subject = 'Passwort zurücksetzen - Videoflix'
    message = f"""
Hallo {user.email},

du hast eine Anfrage zum Zurücksetzen deines Passworts gestellt.

Klicke auf folgenden Link, um ein neues Passwort festzulegen:
{reset_link}

Der Link ist 1 Stunde gültig.

Falls du diese Anfrage nicht gestellt hast, ignoriere diese E-Mail.

Viele Grüße
Dein Videoflix-Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"E-Mail-Versand fehlgeschlagen: {e}")
        return False