from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    """
    full_name = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()

    class Meta:
        model = UserProfile
        fields = [
            'bio', 'birth_date', 'phone_number', 'website', 'avatar',
            'country', 'city', 'is_public', 'show_email',
            'email_notifications', 'marketing_emails',
            'full_name', 'display_name', 'created', 'modified'
        ]
        read_only_fields = ['created', 'modified']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with profile information.
    """
    profile = UserProfileSerializer(read_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'is_active', 'date_joined',
            'last_login', 'profile'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate(self, attrs):
        """
        Validate that passwords match.
        """
        if 'password' in attrs and 'password_confirm' in attrs:
            if attrs['password'] != attrs['password_confirm']:
                raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def validate_email(self, value):
        """
        Validate that email is unique.
        """
        if User.objects.filter(email=value).exists():
            if not self.instance or self.instance.email != value:
                raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """
        Create a new user with encrypted password.
        """
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Update user instance.
        """
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information (without password).
    """
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile']

    def validate_email(self, value):
        """
        Validate that email is unique.
        """
        if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def update(self, instance, validated_data):
        """
        Update user and profile information.
        """
        profile_data = validated_data.pop('profile', {})

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile fields
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    """
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate_current_password(self, value):
        """
        Validate current password.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        """
        Validate that new passwords match.
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords do not match.")
        return attrs

    def save(self):
        """
        Save the new password.
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for Knox-based authentication.
    """
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )

            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')

            if not user.is_active:
                msg = 'User account is disabled.'
                raise serializers.ValidationError(msg, code='authorization')

            attrs['user'] = user
            return attrs
        else:
            msg = 'Must include "username" and "password".'
            raise serializers.ValidationError(msg, code='authorization')


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Serializer for public user information (limited fields).
    """
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'date_joined', 'profile']

    def get_profile(self, obj):
        """
        Get public profile information only.
        """
        if hasattr(obj, 'profile') and obj.profile.is_public:
            return {
                'bio': obj.profile.bio,
                'website': obj.profile.website,
                'country': obj.profile.country,
                'city': obj.profile.city,
                'avatar': obj.profile.avatar.url if obj.profile.avatar else None,
                'full_name': obj.profile.full_name,
                'display_name': obj.profile.display_name,
            }
        return None
