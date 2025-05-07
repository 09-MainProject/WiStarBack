from rest_framework import serializers

from .models import Like


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["id", "content_type", "object_id", "user", "created_at"]
        read_only_fields = ["id", "user", "created_at"]
