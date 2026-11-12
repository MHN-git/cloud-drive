from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction

from quota.models import Quota

User = get_user_model()

class SignUpSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password1', 'password2')

    def validate_username(self, username):
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already exists")
        return username

    def validate(self, attrs):
        password1 = attrs.pop('password1')
        password2 = attrs.pop('password2')
        if password1 != password2:
            raise serializers.ValidationError("Passwords don't match")
        attrs.setdefault('password', password1)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Quota.objects.create(owner=user)

        return user


# class LoginSerializer(serializers.ModelSerializer):
#         username = serializers.CharField(max_length=150)
#         password = serializers.CharField(max_length=128)
#
#         class Meta:
#             model = User
#             fields = ('username', 'password')
#
#         def validate(self, attrs):
#             username = attrs.get('username')
#             password = attrs.get('password')
#
#             user = authenticate(self.context.get('request'), username=username, password=password)
#             if user is None:
#                 raise serializers.ValidationError("Invalid credentials")
#             else:
#                 self.confirm_login_allowed(user)
#
#             return attrs
#
#         def confirm_login_allowed(self, user):
#             if not user.is_active:
#                 raise serializers.ValidationError("User is not active")
#
