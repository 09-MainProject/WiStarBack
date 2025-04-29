from rest_framework import serializers
from .models import Post, Comment
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
        image (ImageField): 게시물 이미지
        image_url (str): 게시물 이미지 URL
        created_at (datetime): 생성 시간
        updated_at (datetime): 수정 시간
        views (int): 조회수
        author (User): 작성자
        comment_count (int): 댓글 수
    """
    author = UserSerializer(read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id',  # 게시물 고유 ID
            'title',  # 게시물 제목
            'content',  # 게시물 내용
            'image',  # 게시물 이미지
            'image_url',  # 게시물 이미지 URL
            'created_at',  # 생성 시간
            'updated_at',  # 수정 시간
            'views',  # 조회수
            'author',  # 작성자
            'comment_count',  # 댓글 수
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'views', 'author', 'comment_count']

    def get_comment_count(self, obj):
        """댓글 수를 반환합니다."""
        return obj.comments.filter(is_deleted=False).count()

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

    def validate_image(self, value):
        """게시물 이미지 유효성 검사"""
        if value:
            # 이미지 크기 제한 (5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("이미지 크기는 5MB를 초과할 수 없습니다.")
            # 이미지 형식 검사
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("이미지 파일만 업로드 가능합니다.")
        return value

    def validate_image_url(self, value):
        """게시물 이미지 URL 유효성 검사"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("올바른 URL 형식이어야 합니다.")
        return value


class CommentSerializer(serializers.ModelSerializer):
    """
    댓글 정보를 직렬화하는 Serializer
    
    Attributes:
        id (int): 댓글 고유 ID
        post (Post): 연결된 게시물
        author (User): 작성자
        content (str): 댓글 내용
        created_at (datetime): 생성 시간
        updated_at (datetime): 수정 시간
        is_deleted (bool): 삭제 여부
        deleted_at (datetime): 삭제 시간
        deleted_by (User): 삭제한 사용자
    """
    author = UserSerializer(read_only=True)
    deleted_by = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',  # 댓글 고유 ID
            'post',  # 연결된 게시물
            'author',  # 작성자
            'content',  # 댓글 내용
            'created_at',  # 생성 시간
            'updated_at',  # 수정 시간
            'is_deleted',  # 삭제 여부
            'deleted_at',  # 삭제 시간
            'deleted_by',  # 삭제한 사용자
        ]
        read_only_fields = ['id', 'post', 'author', 'created_at', 'updated_at', 'is_deleted', 'deleted_at', 'deleted_by']

    def validate_content(self, value):
        """댓글 내용 유효성 검사"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("댓글 내용은 최소 2자 이상이어야 합니다.")
        return value

    def validate(self, data):
        """댓글 데이터 유효성 검사"""
        # 삭제된 댓글은 수정할 수 없음
        if self.instance and self.instance.is_deleted:
            raise serializers.ValidationError("삭제된 댓글은 수정할 수 없습니다.")
        return data