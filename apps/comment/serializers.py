from rest_framework import serializers

from apps.comment.models import Comment
from apps.user.serializers import UsernameSerializer


class CommentSerializer(serializers.ModelSerializer):
    """댓글 시리얼라이저"""

    author = serializers.CharField(source="author.nickname", read_only=True)
    post = serializers.PrimaryKeyRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    parent = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "author",
            "post",
            "parent",
            "created_at",
            "updated_at",
            "replies",
            "likes_count",
            "is_liked",
        ]
        read_only_fields = [
            "id",
            "author",
            "post",
            "parent",
            "created_at",
            "updated_at",
            "replies",
            "likes_count",
            "is_liked",
        ]

    def get_likes_count(self, obj):
        """좋아요 수를 반환합니다."""
        return obj.likes.count()

    def get_is_liked(self, obj):
        """현재 사용자의 좋아요 여부를 반환합니다."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def get_replies(self, obj):
        """대댓글 목록을 반환합니다."""
        if hasattr(obj, "child_comments"):
            replies = obj.child_comments.filter(is_deleted=False).order_by("created_at")
            return CommentSerializer(replies, many=True, context=self.context).data
        return []


class CommentCreateSerializer(serializers.ModelSerializer):
    """댓글 생성 시리얼라이저"""

    class Meta:
        model = Comment
        fields = ["content", "parent"]

    def validate_parent(self, value):
        """부모 댓글의 유효성을 검사합니다."""
        if value:
            if value.is_deleted:
                raise serializers.ValidationError(
                    "삭제된 댓글에는 답글을 달 수 없습니다."
                )
            if value.parent is not None:
                raise serializers.ValidationError("대댓글에는 답글을 달 수 없습니다.")
            if value.post_id != self.context.get("post_id"):
                raise serializers.ValidationError("잘못된 부모 댓글입니다.")
        return value


class CommentUpdateSerializer(serializers.ModelSerializer):
    """댓글 수정 시리얼라이저"""

    class Meta:
        model = Comment
        fields = ["content"]
