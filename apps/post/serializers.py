from rest_framework import serializers
from .models import Post
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class PostSerializer(serializers.ModelSerializer):
    """
    게시물 정보를 직렬화하는 Serializer

    Attributes:
        title (str): 게시물 제목
        content (str): 게시물 내용
        image_url (str): 게시물 이미지 URL
        created_at (datetime): 생성 시간
        updated_at (datetime): 수정 시간
        views (int): 조회수
        author (User): 작성자
    """
    author = UserSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',  # 게시물 고유 ID
            'title',  # 게시물 제목
            'content',  # 게시물 내용
            'image_url',  # 게시물 이미지 URL
            'created_at',  # 생성 시간
            'updated_at',  # 수정 시간
            'views',  # 조회수
            'author',  # 작성자
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'views', 'author']

    def validate_title(self, value):
        """게시물 제목 유효성 검사"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("제목은 최소 2자 이상이어야 합니다.")
        return value

    def validate_content(self, value):
        """게시물 내용 유효성 검사"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("내용은 최소 10자 이상이어야 합니다.")
        return value

    def validate_image_url(self, value):
        """게시물 이미지 URL 유효성 검사"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("올바른 URL 형식이어야 합니다.")
        return value