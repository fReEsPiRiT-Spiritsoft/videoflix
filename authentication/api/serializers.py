from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
import secrets


class RegistrationSerializer(serializers.ModelSerializer):
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
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirmed_password']:
            raise serializers.ValidationError("Password and confirmed password do not match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirmed_password')
        activation_token = secrets.token_urlsafe(32)

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

        user.activation_token = activation_token
        # Here you would typically send an activation email containing the token


        return user
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Ungültige Anmeldedaten.")
        

        if not user.is_active:
            raise serializers.ValidationError("Dein Account ist noch nicht aktiviert. Bitte prüfe deine E-Mails.")
        
        user = authenticate(username=user.username, password=password)
        
        if user is None:
            raise serializers.ValidationError("Ungültige Anmeldedaten.")
        
        attrs['user'] = user
        return attrs