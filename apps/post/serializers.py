from rest_framework import serializers

from apps.user.serializers import UserSerializer

from .models import Post
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class PostSerializer(serializers.ModelSerializer):
    """게시물 시리얼라이저"""

    author = UserSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "content",
            "image",
            "image_url",
            "author",
            "created_at",
            "updated_at",
            "views",
            "is_deleted",
        ]
        read_only_fields = ["author", "created_at", "updated_at", "views", "is_deleted"]


class PostCreateSerializer(serializers.ModelSerializer):
    """게시물 생성 시리얼라이저"""

    class Meta:
        model = Post
        fields = ["title", "content", "image"]


class PostUpdateSerializer(serializers.ModelSerializer):
    """게시물 수정 시리얼라이저"""

    class Meta:
        model = Post
        fields = ["title", "content", "image"]

    def validate_image_url(self, value):
        """이미지 URL 유효성 검사"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("올바른 URL 형식이어야 합니다.")
        return value