from rest_framework import serializers

from apps.user.serializers import UsernameSerializer

from .models import Post


class PostSerializer(serializers.ModelSerializer):
    """
    게시물 시리얼라이저

    게시물의 모든 필드를 포함합니다.
    """

    author = UsernameSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "title",
            "content",
            "image",
            "image_url",
            "created_at",
            "updated_at",
            "views",
            "likes_count",
            "is_liked",
            "is_deleted",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "views",
            "likes_count",
            "is_liked",
            "is_deleted",
        ]

    def get_likes_count(self, obj):
        """좋아요 수를 반환합니다."""
        return obj.likes.count()

    def get_is_liked(self, obj):
        """현재 사용자가 좋아요를 눌렀는지 여부를 반환합니다."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class PostCreateSerializer(serializers.ModelSerializer):
    """
    게시물 생성 시리얼라이저

    게시물 생성에 필요한 필드만 포함합니다.
    """

    class Meta:
        model = Post
        fields = ["title", "content", "image", "image_url"]


class PostUpdateSerializer(serializers.ModelSerializer):
    """
    게시물 수정 시리얼라이저

    게시물 수정에 필요한 필드만 포함합니다.
    """

    class Meta:
        model = Post
        fields = ["title", "content", "image", "image_url"]
