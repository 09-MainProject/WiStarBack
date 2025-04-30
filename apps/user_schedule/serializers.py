from rest_framework import serializers

from .models import UserSchedule


class UserScheduleSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()

    class Meta:
        model = UserSchedule
        fields = [
            "id",
            "title",
            "description",
            "location",
            "start_date",
            "end_date",
            "date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "date"]

    def get_date(self, obj):
        return obj.start_date.date()
