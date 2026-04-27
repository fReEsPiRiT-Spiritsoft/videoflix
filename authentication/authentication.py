"""Custom JWT authentication backend for cookie-based token authentication.

This module provides a custom JWT authentication class that reads tokens from
HTTP-only cookies instead of the standard Authorization header, enhancing
security for web applications.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication that reads tokens from cookies.
    
    This authentication class extends the standard JWT authentication to read
    the access token from HTTP-only cookies instead of the Authorization header,
    providing better security against XSS attacks.
    """
    
    def authenticate(self, request):
        """Authenticate the request using JWT token from cookies.
        
        Args:
            request: The HTTP request object containing cookies.
            
        Returns:
            tuple: (user, validated_token) if authentication succeeds.
            None: If no token is found or authentication fails.
        """
        access_token = request.COOKIES.get('access_token')
        
        if access_token is None:
            return None
        
        validated_token = self.get_validated_token(access_token)
        
        try:
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            return None