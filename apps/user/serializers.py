from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """사용자 시리얼라이저"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email'] 