"""Authentication models for user account activation and password reset.

This module contains token-based models for secure user authentication flows,
including account activation and password reset functionality.
"""

from django.db import models
from django.contrib.auth.models import User
import secrets
from django.utils import timezone
from datetime import timedelta


class ActivationToken(models.Model):
    """Token model for email-based account activation.
    
    This model stores secure tokens that are sent to users via email to verify
    their email address and activate their account. Tokens are valid for 24 hours.
    
    Attributes:
        user: OneToOne relationship to the User being activated.
        token: Unique cryptographically secure token string.
        created_at: Timestamp of token creation for expiry validation.
    """
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='activation_token')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Activation Token"
        verbose_name_plural = "Activation Tokens"
    
    def __str__(self):
        return f"Token for {self.user.email}"
    
    def is_valid(self):
        """Check if the token is still valid (24 hours from creation).
        
        Returns:
            bool: True if token is within 24-hour validity period.
        """
        expiry_time = self.created_at + timedelta(hours=24)
        return timezone.now() < expiry_time
    
    @staticmethod
    def generate_token():
        """Generate a cryptographically secure random token.
        
        Returns:
            str: URL-safe random token string.
        """
        return secrets.token_urlsafe(32)
    


class PasswordResetToken(models.Model):
    """Token model for secure password reset functionality.
    
    This model stores one-time use tokens for password reset requests.
    Tokens expire after 1 hour and can only be used once for security.
    
    Attributes:
        user: Foreign key to the User requesting password reset.
        token: Unique cryptographically secure token string.
        created_at: Timestamp of token creation for expiry validation.
        used: Flag indicating whether the token has been consumed.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
    
    def __str__(self):
        return f"Password Reset Token for {self.user.email}"
    
    def is_valid(self):
        """Check if the token is valid and not yet used.
        
        A token is valid if:
        - It has not been used yet
        - It is within the 1-hour validity period
        
        Returns:
            bool: True if token is valid and usable.
        """
        if self.used:
            return False
        expiry_time = self.created_at + timedelta(hours=1)
        return timezone.now() < expiry_time
    
    @staticmethod
    def generate_token():
        """Generate a cryptographically secure random token.
        
        Returns:
            str: URL-safe random token string.
        """
        return secrets.token_urlsafe(32)