from rest_framework import serializers

from .models import Like


class LikeSerializer(serializers.ModelSerializer):
    """좋아요 Serializer"""

    class Meta:
        model = Like
        fields = ["id", "user", "post", "created_at"]
        read_only_fields = ["user", "created_at"]
