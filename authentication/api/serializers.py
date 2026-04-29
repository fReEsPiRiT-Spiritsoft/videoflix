"""Serializers for user authentication API endpoints.

This module provides DRF serializers for user registration, login, and
password reset operations with validation and error handling.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from authentication.models import ActivationToken
from authentication.utils import send_activation_email


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with email verification.
    
    Handles user account creation with password validation and sends
    activation email with token for email verification.
    
    Fields:
        email: User's email address (required, unique).
        password: User's password (write-only, validated).
        confirmed_password: Password confirmation (write-only).
        token: Activation token (read-only, auto-generated).
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirmed_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password', 'token']
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate_email(self, value):
        """Validate that email is not already registered.
        
        Args:
            value: Email address to validate.
            
        Returns:
            str: Lowercase email address.
            
        Raises:
            ValidationError: If email is already registered.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate(self, attrs):
        """Validate that passwords match.
        
        Args:
            attrs: Dictionary of field values.
            
        Returns:
            dict: Validated attributes.
            
        Raises:
            ValidationError: If passwords don't match.
        """
        if attrs['password'] != attrs['confirmed_password']:
            raise serializers.ValidationError("Password and confirmed password do not match.")
        return attrs
    
    def create(self, validated_data):
        """Create inactive user and send activation email.
        
        Args:
            validated_data: Validated serializer data.
            
        Returns:
            User: Created user object with activation token.
        """
        validated_data.pop('confirmed_password')
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False
        )

        activation_token = ActivationToken.objects.create(
            user=user,
            token=ActivationToken.generate_token()
        )
        user.activation_token_value = activation_token.token
   
        send_activation_email(user, activation_token.token)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login authentication.
    
    Validates user credentials and checks account activation status.
    
    Fields:
        email: User's email address (required).
        password: User's password (write-only, required).
    """
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate credentials and account activation status.
        
        Args:
            attrs: Dictionary containing email and password.
            
        Returns:
            dict: Validated attributes with user object.
            
        Raises:
            ValidationError: If credentials invalid or account not activated.
        """
        email = attrs.get('email')
        password = attrs.get('password')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.")
        
        if not user.is_active:
            raise serializers.ValidationError(
                "Your account is not yet activated. Please check your email."
            )
        
        user = authenticate(username=user.username, password=password)
        
        if user is None:
            raise serializers.ValidationError("Invalid credentials.")
        
        attrs['user'] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request.
    
    Validates that the email exists and account is active before
    sending password reset email.
    
    Fields:
        email: User's email address (required).
    """
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate that user exists and account is active.
        
        Args:
            value: Email address to validate.
            
        Returns:
            str: Lowercase email address.
            
        Raises:
            ValidationError: If account is not activated.
            
        Note:
            Does not raise error for non-existent emails to prevent
            email enumeration attacks.
        """
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError("Your account is not activated.")
        except User.DoesNotExist:
            pass
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset.
    
    Fields:
        new_password: New password (write-only, validated).
    """
    
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )