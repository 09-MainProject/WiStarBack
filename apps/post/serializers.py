from rest_framework import serializers

from apps.user.serializers import UsernameSerializer

from .models import Post


class PostSerializer(serializers.ModelSerializer):
    """게시물 시리얼라이저"""

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
            "created_at",
            "updated_at",
            "views",
            "likes_count",
            "is_liked",
            "is_deleted",
            "image",
            "image_url",
        ]
        read_only_fields = ["author", "created_at", "updated_at", "views"]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False


class PostCreateSerializer(serializers.ModelSerializer):
    """게시물 생성 시리얼라이저"""

    author = UsernameSerializer(read_only=True)

    class Meta:
        model = Post
        fields = ["title", "content", "image", "image_url", "author"]
        read_only_fields = ["author"]

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


class PostUpdateSerializer(serializers.ModelSerializer):
    """게시물 수정 시리얼라이저"""

    class Meta:
        model = Post
        fields = ["title", "content", "image"]
