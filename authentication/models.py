from django.db import models
from django.contrib.auth.models import User
import secrets
from django.utils import timezone
from datetime import timedelta


class ActivationToken(models.Model):

    pass


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Passwort-Zurücksetzen-Token"
        verbose_name_plural = "Passwort-Zurücksetzen-Tokens"
    
    def __str__(self):
        return f"Password Reset Token für {self.user.email}"
    
    def is_valid(self):
        """Token ist 1 Stunde gültig und darf nicht bereits verwendet sein"""
        if self.used:
            return False
        expiry_time = self.created_at + timedelta(hours=1)
        return timezone.now() < expiry_time
    
    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)