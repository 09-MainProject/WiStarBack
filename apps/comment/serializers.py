from rest_framework import serializers

from apps.user.serializers import UsernameSerializer

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    """댓글 시리얼라이저"""

    author = UsernameSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "post",
            "author",
            "content",
            "created_at",
            "updated_at",
            "is_deleted",
            "likes_count",
            "is_liked",
        ]
        read_only_fields = [
            "author",
            "created_at",
            "updated_at",
            "is_deleted",
            "likes_count",
            "is_liked",
        ]

    def get_is_liked(self, obj):
        """현재 사용자의 좋아요 여부를 반환합니다."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.is_liked_by(request.user)
        return False


class CommentCreateSerializer(serializers.ModelSerializer):
    """댓글 생성 시리얼라이저"""

    class Meta:
        model = Comment
        fields = ["content"]


class CommentUpdateSerializer(serializers.ModelSerializer):
    """댓글 수정 시리얼라이저"""

    class Meta:
        model = Comment
        fields = ["content"]
