from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication, die Token aus Cookies liest statt aus dem Authorization-Header
    """
    def authenticate(self, request):
        # Versuche zuerst Token aus Cookie zu lesen
        access_token = request.COOKIES.get('access_token')
        
        if access_token is None:
            return None
        
        # Validiere Token
        validated_token = self.get_validated_token(access_token)
        
        try:
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            return None