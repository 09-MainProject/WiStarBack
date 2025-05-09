# apps/follow/serializers.py
from rest_framework import serializers

from apps.follow.models import Follow


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ["id", "user", "idol", "created_at"]
        read_only_fields = ["id", "user", "created_at"]
