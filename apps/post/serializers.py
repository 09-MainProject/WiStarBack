from rest_framework import serializers
from .models import Post
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class PostSerializer(serializers.ModelSerializer):

    author = UserSerializer(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'image_url', 'created_at', 
                 'updated_at', 'views', 'author']
        read_only_fields = ['created_at', 'updated_at', 'views', 'author']

    def validate_title(self, value):
        """제목 유효성 검사"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("제목은 최소 2자 이상이어야 합니다.")
        return value

    def validate_content(self, value):
        """내용 유효성 검사"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("내용은 최소 10자 이상이어야 합니다.")
        return value

    def validate_image_url(self, value):
        """이미지 URL 유효성 검사"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("올바른 URL 형식이어야 합니다.")
        return value