# apps/follow/serializers.py
from rest_framework import serializers

from apps.follow.models import Follow
from apps.idol.models import Idol


class IdolSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Idol
        fields = ["id", "name", "en_name", "agency"]


class FollowSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    idol = IdolSimpleSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ["id", "user_id", "idol", "created_at"]
        read_only_fields = ["id", "user_id", "idol", "created_at"]
